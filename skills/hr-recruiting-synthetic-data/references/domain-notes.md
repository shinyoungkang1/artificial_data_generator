# HR Recruiting Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `candidate_id` | string | `CAN-500000` to `CAN-{500000+rows-1}`, sequential | Yes |
| `job_req_id` | string | `REQ-10000` to `REQ-99999`, random | Yes |
| `application_date` | string (ISO date) | today minus 1-300 days | Yes |
| `candidate_name` | string | Alex Kim, Jordan Patel, Casey Brown, Taylor Nguyen, Riley Garcia | Yes |
| `email` | string | `candidateN@example.org` (N = row index) | Yes |
| `location` | string | Austin,TX; Chicago,IL; Miami,FL; Seattle,WA; Remote | Yes |
| `source_channel` | string | job_board, referral, career_site, agency, internal_mobility | Yes |
| `current_stage` | string | applied, screen, interview, panel, offer, hired, rejected | Yes |
| `interview_score` | float or string | 1.0 to 10.0; may be `"X/10"`/`"n/a"` | Yes |
| `offer_status` | string | none, pending, accepted, declined | Yes |
| `expected_salary_usd` | float or string | 45,000 to 320,000; may be `$XX,XXX.XX` | Yes |
| `recruiter_id` | string | `REC-100` to `REC-999` | Yes |
| `notes` | string | clean, resume unclear, rescheduled, duplicate profile | Yes |

## Business Rules and Invariants

1. **Candidate ID uniqueness**: `candidate_id` is sequential (`CAN-500000 + i`),
   guaranteed unique within a single generation run.
2. **Email uniqueness**: `email` uses the row index (`candidate{i}@example.org`),
   so it is unique per run.
3. **Score range**: Interview scores are 1.0-10.0 in clean rows. Messy rows may
   produce `"n/a"` for unscored candidates.
4. **Salary range**: Expected salary is $45,000-$320,000 in clean rows.
5. **Stage-offer independence**: `current_stage` and `offer_status` are generated
   independently. The generator does NOT enforce that only "offer"-stage
   candidates have non-"none" offer statuses. This is intentional.
6. **Job req collisions**: `job_req_id` is randomly generated and may repeat
   across rows (multiple candidates applying for the same position).
7. **Limited name pool**: Only 5 distinct names are used. Name is not a reliable
   deduplication key.

## Mess Pattern Deep Dive

### Stage label drift (weight 0.30)
- **Simulates**: Different ATS versions, recruiter manual edits, or imported
  data from partner agencies using non-standard stage names.
- **Values injected**: `Screen` (title case), `onsite` (non-standard label for
  in-person interview), `panel ` (trailing space), `offer?` (uncertainty
  marker), `archive` (non-standard disposition stage).
- **Downstream failures**: Funnel stage mapping breaks, conversion rate
  calculations produce wrong denominators, pipeline velocity metrics skip
  unmapped stages, JOIN to stage-configuration tables returns NULLs.

### Interview score encoding (weight 0.24)
- **Simulates**: ATS export formats varying across modules or import sources.
  Some systems export scores as fractions, others as plain text.
- **Three variants**: `"7.5"` (string instead of float), `"7.5/10"` (fraction
  notation), `"n/a"` (not applicable / not yet scored).
- **Downstream failures**: `float()` conversion raises ValueError, average
  score calculations include string values, sorting by score produces
  lexicographic instead of numeric order.

### Currency-formatted salary (weight 0.20)
- **Simulates**: Salary expectations imported from recruiter notes or external
  job boards that format numbers with currency symbols.
- **Manifestation**: Float `85000.00` becomes string `$85,000.00`.
- **Downstream failures**: Salary range filters exclude currency-formatted rows,
  compensation analytics produce incorrect averages, budget planning queries
  silently drop non-numeric values.

### Missing source channel (weight 0.16)
- **Simulates**: Imported candidate records from career fairs, email
  applications, or legacy ATS migrations where source tracking was incomplete.
- **Values injected**: empty string `""`, `"unknown"`, or the original value
  (each with ~1/3 probability when triggered).
- **Downstream failures**: Source attribution reports undercount channels,
  ROI calculations for recruiting spend miss candidates, source-based
  funnel analysis has incomplete data.

## Real-World Context

This data mimics exports from applicant tracking systems like Greenhouse,
Lever, Workday Recruiting, iCIMS, or Taleo. In production, recruiting data
arrives via ATS API exports, scheduled CSV/SFTP drops, or manual recruiter
spreadsheet uploads.

Typical consumers are talent acquisition teams tracking pipeline health,
hiring managers reviewing candidate pools, HR analytics teams measuring
time-to-fill and source effectiveness, and compensation teams benchmarking
salary expectations against internal pay bands.

## Cross-Skill Relationships

| Related Skill | Shared Fields | Relationship |
|--------------|--------------|-------------|
| `hr-payroll-synthetic-data` | `employee_id` (conceptual) | Hired candidates transition into payroll as employees |
| `hr-employee-file-docs-synthetic-data` | `candidate_name`, `email` | Scanned offer letters and onboarding docs reference candidate records |

**Recommended generation order**: Generate recruiting data first (establishes
candidate pipeline), then payroll for hired candidates, then employee file
docs for onboarding paperwork extraction testing.
