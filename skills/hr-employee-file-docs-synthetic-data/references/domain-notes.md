# HR Employee File OCR Domain Notes

## Document Content Fields

Each synthetic employee file contains the following fields, rendered as
plain-text key-value lines:

| Field | Generator Logic | Example Value |
|-------|----------------|---------------|
| EMPLOYEE_FILE_ID | Sequential `EFILE-{06d}` | `EFILE-000023` |
| Employee ID | Random `EMP-{10000..99999}` | `EMP-57180` |
| Employee Name | Random choice: Alex Kim, Jordan Patel, Casey Brown, Taylor Nguyen | `Jordan Patel` |
| Department | Random choice: Engineering, Sales, Finance, HR, Operations | `Finance` |
| Job Title | Random choice: Analyst, Manager, Specialist, Coordinator, Lead | `Specialist` |
| Hire Date | `20{randint(10,25)}-MM-DD` | `2018-03-21` |
| Employment Status | Random choice: active, leave, pending-change | `active` |
| Pay Grade | Random choice: P2, P3, P4, M1, M2 | `P3` |
| Manager ID | Random `MGR-{1000..9999}` | `MGR-4821` |
| Compliance Training | Random choice: complete, incomplete, expired | `complete` |
| Background Check | Random choice: clear, pending, review | `clear` |
| Notes | Random choice: clean file, updated address, manual correction, signature unclear | `clean file` |

## Visual Layout

The rendered document follows this structure:

**Header** (bold, 12pt Helvetica-Bold):
- Title: "Synthetic Employee File Summary"
- Positioned at (50, height-50) on PDF canvas

**Body** (10pt Helvetica, 14px line spacing PDF / 18px PNG):
- Each field rendered as `FIELD_NAME: value` on its own line
- Starting at y=height-85 (PDF) or y=82 (PNG, after 32px title offset)
- 12 content lines total

**Dimensions**:
- PDF: US Letter (612 x 792 points)
- PNG: 1650 x 2200 pixels, white background
- Font: Helvetica (PDF), Pillow default (PNG)

## Degradation Parameters

The `degrade_image()` function applies four sequential transformations:

### 1. Rotation
- Range: `uniform(-5, 5) * messiness` degrees
- Fill: white for exposed corners (`expand=True`)
- At messiness=0.5: up to ~2.5 degrees
- At messiness=0.95: up to ~4.75 degrees

### 2. Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.5) * messiness)`
- At messiness=0.5: radius 0.2 to 0.75
- At messiness=0.95: radius 0.2 to 1.43

### 3. Contrast Reduction
- Factor: `max(0.5, 1.0 - uniform(0.15, 0.5) * messiness)`
- Uses `ImageEnhance.Contrast`
- At messiness=0.5: contrast factor 0.75 to 0.93
- At messiness=0.95: contrast factor 0.53 to 0.86

### 4. Speckle Noise
- Count: `int(width * height * 0.0008 * messiness) + 70`
- Tone: random grayscale in [0, 120]
- At messiness=0.5 on 1650x2200: ~1522 speckles
- At messiness=0.95 on 1650x2200: ~2823 speckles

## Real-World Context

These synthetic documents simulate scanned employee personnel files that HR
departments maintain for each employee. Real employee files contain:

- Personal identification (name, employee ID, SSN)
- Employment details (department, title, hire date, status)
- Compensation information (pay grade, salary history)
- Compliance records (training completion, background checks)
- Manager chain and organizational structure
- Handwritten notes and annotations from HR staff

The synthetic version covers core personnel fields plus a notes field. The
OCR challenge comes from:

- Employee IDs (EMP-XXXXX) where single-digit errors link to wrong records
- Hire dates spanning 15 years (2010-2025) where year digits are critical
- Employment status values that are similar strings (active vs leave)
- Pay grade codes (P2/P3/P4/M1/M2) where character confusion changes level
- Free-text notes that may contain handwritten-style artifacts

Common OCR failure modes on real employee files:
- `EMP-57180` misread as `EMP-57180` vs `EMP-57188` (0/8 confusion)
- Hire date `2018-03-21` misread as `2013-03-21` (8/3 confusion)
- Pay grade `P3` misread as `P8` or `P2` under low contrast
- Status `pending-change` truncated or hyphen lost in degraded scan
- Manager ID `MGR-4821` confused with employee ID formatting

## Cross-Skill Relationships

| This Skill Field | Related Tabular Skill | Related Field |
|-----------------|----------------------|---------------|
| Employee ID (EMP-XXXXX) | hr-payroll-synthetic-data | employee_id |
| Employee Name | hr-recruiting-synthetic-data | candidate_name |
| Department | hr-payroll-synthetic-data | department |
| Hire Date | hr-payroll-synthetic-data | hire_date |
| Pay Grade | hr-payroll-synthetic-data | pay_grade |
| Manager ID | hr-payroll-synthetic-data | manager_id |

Use the tabular skills to generate ground-truth structured data, then
compare OCR-extracted values from employee file documents against those
tables to measure extraction accuracy.
