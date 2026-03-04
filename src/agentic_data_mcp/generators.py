"""Domain record generators for clean and messy synthetic rows."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from .utils import optional_import

INDUSTRIES = [
    "Manufacturing",
    "Healthcare",
    "Retail",
    "FinTech",
    "Logistics",
    "Software",
    "Energy",
    "Construction",
    "Telecom",
]

COUNTRIES = ["US", "CA", "MX", "DE", "FR", "JP", "KR", "IN", "BR"]
INVOICE_STATUS = ["paid", "pending", "overdue", "void", "refunded"]
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"]
NOISY_NOTES = [
    "PO attached",
    "see thread #A12",
    "invoice scan low quality",
    "check signature ???",
    "urgent follow-up",
    "acct moved to new owner",
    "manual override",
    "received via fax",
]


def generate_company_records(
    count: int,
    seed: int = 7,
    messiness: float = 0.35,
) -> list[dict[str, Any]]:
    """Generate realistic company/invoice rows with controlled messiness."""
    rng = random.Random(seed)
    faker_module, _ = optional_import("faker")
    fake = None
    if faker_module:
        fake = faker_module.Faker()
        fake.seed_instance(seed)

    rows: list[dict[str, Any]] = []
    base_date = date.today() - timedelta(days=240)

    for i in range(max(1, count)):
        issued = base_date + timedelta(days=rng.randint(0, 220))
        due = issued + timedelta(days=rng.randint(15, 60))
        amount = round(rng.uniform(300, 120000), 2)
        employees = rng.randint(4, 12000)

        if fake:
            company_name = fake.company()
            contact = fake.name()
            email = fake.company_email()
            address = fake.address().replace("\n", ", ")
        else:
            company_name = f"{rng.choice(['North', 'Global', 'Prime', 'Delta', 'Union'])} {rng.choice(['Dynamics', 'Systems', 'Works', 'Foods', 'Energy'])} LLC"
            contact = f"{rng.choice(['J.', 'K.', 'L.', 'M.'])} {rng.choice(['Kim', 'Patel', 'Brown', 'Garcia', 'Nguyen'])}"
            email = f"ops{i:04d}@example.org"
            address = f"{rng.randint(100, 9999)} {rng.choice(['Main', 'Maple', 'Sunset', 'Pine'])} St"

        row: dict[str, Any] = {
            "row_id": i + 1,
            "company_id": f"CMP-{100000 + i}",
            "company_name": company_name,
            "industry": rng.choice(INDUSTRIES),
            "country": rng.choice(COUNTRIES),
            "employee_count": employees,
            "annual_revenue_usd": amount * rng.uniform(6, 40),
            "invoice_id": f"INV-{rng.randint(200000, 999999)}",
            "invoice_date": issued.strftime(rng.choice(DATE_FORMATS)),
            "due_date": due.strftime(rng.choice(DATE_FORMATS)),
            "invoice_amount_usd": amount,
            "status": rng.choice(INVOICE_STATUS),
            "contact_name": contact,
            "contact_email": email,
            "address": address,
            "notes": rng.choice(NOISY_NOTES),
        }
        apply_record_mess(row, rng, messiness)
        rows.append(row)

        if rows and rng.random() < messiness * 0.08:
            duplicate = dict(rows[-1])
            duplicate["row_id"] = f"{duplicate['row_id']}-dup"
            if rng.random() < 0.7:
                duplicate["notes"] = f"{duplicate['notes']} / duplicate from email chain"
            rows.append(duplicate)

    return rows


def apply_record_mess(row: dict[str, Any], rng: random.Random, messiness: float) -> None:
    """Inject realistic inconsistencies directly into a row."""
    if rng.random() < messiness * 0.5:
        row["notes"] = row["notes"] + rng.choice(["", " !!!", " ...", " (unclear)"])

    if rng.random() < messiness * 0.45:
        row["invoice_amount_usd"] = noisy_number(row["invoice_amount_usd"], rng)

    if rng.random() < messiness * 0.3:
        row["annual_revenue_usd"] = noisy_number(row["annual_revenue_usd"], rng)

    if rng.random() < messiness * 0.35:
        null_key = rng.choice(
            [
                "contact_email",
                "address",
                "employee_count",
                "industry",
                "due_date",
                "notes",
            ]
        )
        row[null_key] = rng.choice(["", "N/A", None, "unknown"])

    if rng.random() < messiness * 0.28:
        row["status"] = rng.choice(["Paid", "PAID", "pending ", "over-due", "void?"])

    if rng.random() < messiness * 0.18:
        row["company_name"] = typo_text(str(row["company_name"]), rng)

    if rng.random() < messiness * 0.16:
        row["contact_name"] = f"{row['contact_name']} / {row['contact_name']}".strip()


def noisy_number(value: Any, rng: random.Random) -> Any:
    base = float(value)
    style = rng.choice(["plain", "commas", "currency", "rounded", "spaces", "scientific"])
    if style == "plain":
        return round(base, 2)
    if style == "commas":
        return f"{base:,.2f}"
    if style == "currency":
        return rng.choice(["$", "USD "]) + f"{base:,.2f}"
    if style == "rounded":
        return str(round(base))
    if style == "spaces":
        return f" {base:.2f} "
    return f"{base:.2e}"


def typo_text(value: str, rng: random.Random) -> str:
    if len(value) < 4:
        return value
    op = rng.choice(["drop", "swap", "repeat", "case"])
    idx = rng.randint(1, len(value) - 2)
    if op == "drop":
        return value[:idx] + value[idx + 1 :]
    if op == "swap":
        chars = list(value)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return "".join(chars)
    if op == "repeat":
        return value[:idx] + value[idx] + value[idx:]
    return value[:idx] + value[idx].upper() + value[idx + 1 :]

