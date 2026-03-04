# HR Time and Attendance Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `attendance_id` | str | `TATT-2400000` onward, sequential | yes | Unique per row |
| `employee_id` | str | `EMP-10000` to `EMP-99999` | yes | Random, not unique |
| `department` | str | 8 departments | yes | Clean |
| `work_date` | str | ISO date, today minus 1-365 days | yes | Clean |
| `clock_in` | str | `HH:MM` format, shift-dependent | yes | Clean |
| `clock_out` | str | `HH:MM` format | yes | Blank when messy |
| `hours_worked` | float | ~0.0--11.0 (shift minus break) | yes | "h"/"hrs" suffix when messy |
| `break_minutes` | int | 0, 15, 30, 45, 60 | yes | Clean |
| `overtime_hours` | float | `max(0, hours_worked - 8)` | yes | Clean, derived |
| `attendance_type` | str | 7 types | yes | Casing/shorthand when messy |
| `shift` | str | `day`, `swing`, `night`, `split` | yes | Clean |
| `location` | str | 8 office/warehouse locations | yes | Clean |
| `supervisor_id` | str | `EMP-10000` to `EMP-99999` | yes | Clean |
| `approved` | str | `yes`, `no` | yes | Y/N/1/0/true when messy |
| `pay_code` | str | `REG`, `OT`, `HOL`, `PTO`, `SICK`, `LWOP` | yes | Clean |
| `notes` | str | `clean`, `late arrival`, `early departure`, `shift swap` | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Time calculation (clean rows)
- `hours_worked ~ (clock_out - clock_in) - break_minutes / 60`
- Approximate because clock times are rounded to minutes
- `hours_worked >= 0` always holds

### Overtime rule
- `overtime_hours = max(0.0, hours_worked - 8.0)`
- Overtime is derived, not independently randomized

### Shift-based clock-in
- Day shift: clock_in between 06:00 and 09:59
- Swing shift: clock_in between 14:00 and 16:59
- Night shift: clock_in between 21:00 and 23:59
- Split shift: clock_in between 07:00 and 09:59

### Uniqueness
- `attendance_id` is globally unique (sequential: `TATT-2400000`, `TATT-2400001`, ...)
- `employee_id` and `supervisor_id` may repeat

## Mess Pattern Deep Dive

### attendance_type (weight 0.28)
- **What it simulates**: HRIS feed consolidation where different time tracking platforms use different casing and abbreviations for attendance types.
- **Messy values**: `Regular` (title case), `OT` (abbreviation), `Sick Leave` (two words with space), `WFH ` (trailing space)
- **Downstream failure**: Enum validation rejects non-standard values; attendance-based pay code mapping breaks.

### hours_worked (weight 0.24)
- **What it simulates**: Time tracking exports that include unit suffixes in numeric fields.
- **Messy values**: `"8.0h"` (h suffix), `"8.0 hrs"` (hrs suffix)
- **Downstream failure**: `float(value)` raises ValueError; payroll hours aggregation breaks.

### clock_out (weight 0.20)
- **What it simulates**: Missing clock-out punches for employees who forgot to clock out, or shifts still in progress.
- **Messy value**: Empty string `""`
- **Downstream failure**: Hours calculation crashes on empty time; shift duration cannot be derived.

### approved (weight 0.16)
- **What it simulates**: Boolean encoding inconsistencies where different HRIS platforms represent approval as yes/no, Y/N, 1/0, or true/false.
- **Messy values**: `"Y"`, `"N"`, `"1"`, `"0"`, `"true"`
- **Downstream failure**: String equality checks fail; boolean coercion logic varies by encoding.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated time tracking exception reports.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based exception handling logic breaks; pattern matching fails.

## Real-World Context

Time and attendance data flows through multiple systems in the HR ecosystem:

- **Time clock/badge reader**: Employee punches in/out at physical or virtual terminal
- **Time tracking software**: Aggregates punches, calculates hours, applies shift rules
- **HRIS platform**: Consolidates attendance data with employee records
- **Payroll system**: Uses approved hours and pay codes for compensation calculation

Each integration step introduces potential format drift: different time clock vendors
export hours with unit suffixes, approval status encoding varies by HRIS platform,
and attendance type codes differ between time tracking and payroll systems.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `employee_id` | hr-payroll-synthetic-data | `employee_id` | Payroll hours reconciliation |
| `employee_id` | hr-recruiting-synthetic-data | candidate/employee link | Post-hire attendance tracking |
| `department` | hr-employee-file-docs-synthetic-data | department reference | Employee file department alignment |

**Recommended generation order:**
1. Generate employee file docs (establishes employee identities)
2. Generate recruiting records (tracks hire pipeline)
3. Generate payroll and time attendance (reference employee IDs)

Note: The current generators do not enforce referential integrity across skills.
Employee IDs in time attendance are randomly generated. For cross-skill testing,
post-process to align shared identifiers.
