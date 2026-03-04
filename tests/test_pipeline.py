from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentic_data_mcp.generators import generate_company_records
from agentic_data_mcp.pipeline import expand_from_seeds, plan_campaign
from agentic_data_mcp.seed_expand import expand_rows


class PipelineTests(unittest.TestCase):
    def test_generate_company_records(self) -> None:
        rows = generate_company_records(count=10, seed=11, messiness=0.3)
        self.assertGreaterEqual(len(rows), 10)
        self.assertIn("company_name", rows[0])
        self.assertIn("invoice_id", rows[0])

    def test_expand_rows_multiplier(self) -> None:
        seeds = [
            {"row_id": "1", "company_name": "Acme LLC", "invoice_amount_usd": "1200.50"},
            {"row_id": "2", "company_name": "Delta Co", "invoice_amount_usd": "980.10"},
        ]
        expanded = expand_rows(seeds, multiplier=3, messiness=0.2, seed=5)
        self.assertEqual(len(expanded), 6)
        self.assertIn("company_name", expanded[0])

    def test_expand_from_seeds_reads_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            seed_csv = Path(tmp) / "seed.csv"
            seed_csv.write_text(
                "row_id,company_name,invoice_amount_usd\n1,Acme LLC,1000\n2,Zen Corp,2200\n",
                encoding="utf-8",
            )
            result = expand_from_seeds(
                seed_paths=[str(seed_csv)],
                output_dir=tmp,
                multiplier=2,
                messiness=0.25,
                seed=3,
            )
            self.assertIn("generated_row_count", result)
            self.assertEqual(result["generated_row_count"], 4)

    def test_plan_campaign_shape(self) -> None:
        plan = plan_campaign(domain="company-ops", volume=42, messiness=0.55)
        self.assertIn("plan", plan)
        self.assertEqual(plan["plan"]["volume"], 42)


if __name__ == "__main__":
    unittest.main()

