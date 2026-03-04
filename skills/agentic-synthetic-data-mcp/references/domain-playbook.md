# Domain Playbook

Use this strategy to preserve realism while scaling fake data volume.

## 1. Start from a domain contract

Define:

- Entities (company, employee, invoice, purchase order, shipment)
- Relationships (company -> invoices, invoices -> line items)
- Required fields and plausible optional fields
- Value ranges and business constraints

## 2. Build clean canonical rows first

Generate a truthful baseline dataset before corruption:

- Maintain key consistency (`company_id`, `invoice_id`)
- Keep temporal logic valid (`invoice_date` <= `due_date`)
- Keep numeric ranges plausible

## 3. Apply mess layers after canonical generation

Use post-processing transforms so you can toggle mess intensity without losing baseline truth.

## 4. Expand from seed samples

When real-ish samples exist:

1. Read CSV/JSON seeds.
2. Infer schema and observed value distributions.
3. Sample and perturb values with controlled randomness.
4. Preserve critical invariants.
5. Emit manifest with warnings.

## 5. Validate generated data

Check:

- Parser success rates by artifact type
- OCR confidence degradation by recipe
- Schema validation failures
- Entity linking errors after corruption

