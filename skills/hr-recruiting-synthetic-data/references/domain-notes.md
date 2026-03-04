# HR Recruiting Domain Notes

## Core fields

- `candidate_id`, `job_req_id`, `application_date`
- `candidate_name`, `email`, `location`
- `source_channel`, `current_stage`, `interview_score`
- `offer_status`, `expected_salary_usd`, `recruiter_id`, `notes`

## Mess patterns

- stage value drift and custom stage names
- duplicate candidates from reapplication
- interview score mixed numeric/string values
- expected salary formats with currency symbols and commas
- missing recruiter or source values in imported rows
