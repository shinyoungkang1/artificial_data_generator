"""Small CLI for local campaign runs without MCP clients."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import expand_from_seeds, plan_campaign, run_campaign


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic synthetic data MCP local CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan_cmd = sub.add_parser("plan", help="Generate a campaign plan JSON")
    plan_cmd.add_argument("--domain", default="company-ops")
    plan_cmd.add_argument("--volume", type=int, default=500)
    plan_cmd.add_argument("--messiness", type=float, default=0.35)
    plan_cmd.add_argument("--output", default="plan.json")

    gen_cmd = sub.add_parser("generate", help="Generate artifacts from a plan JSON")
    gen_cmd.add_argument("--plan", required=True, help="Path to plan JSON")
    gen_cmd.add_argument("--output-dir", default="./runs")

    exp_cmd = sub.add_parser("expand", help="Expand synthetic rows from seed files")
    exp_cmd.add_argument("--seed", nargs="+", required=True, help="CSV/JSON seed paths")
    exp_cmd.add_argument("--output-dir", default="./runs")
    exp_cmd.add_argument("--multiplier", type=int, default=5)
    exp_cmd.add_argument("--messiness", type=float, default=0.35)

    args = parser.parse_args()

    if args.cmd == "plan":
        payload = plan_campaign(
            domain=args.domain,
            volume=args.volume,
            messiness=args.messiness,
        )
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(args.output)
        return

    if args.cmd == "generate":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        result = run_campaign(plan_payload=plan, output_dir=args.output_dir)
        print(json.dumps(result, indent=2))
        return

    result = expand_from_seeds(
        seed_paths=args.seed,
        output_dir=args.output_dir,
        multiplier=args.multiplier,
        messiness=args.messiness,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

