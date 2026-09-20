# Copyright 2026 The Handoff Authors
# SPDX-License-Identifier: Apache-2.0
"""Read-only check that every AWS resource Handoff depends on is live.

    python scripts/aws_live_check.py            # uses AWS_REGION, default ap-northeast-2

Makes describe/list calls only; account ids are masked in the output.
"""

from __future__ import annotations

import datetime
import os
import re

import boto3

REGION = os.environ.get("AWS_REGION", "ap-northeast-2")


def mask(text: str) -> str:
    return re.sub(r"\d{12}", "9410********", text)


def main() -> int:
    s = boto3.Session(region_name=REGION)
    control = s.client("bedrock-agentcore-control")
    ddb = s.client("dynamodb")

    def table() -> str:
        t = ddb.describe_table(TableName="handoff")["Table"]
        keys = "+".join(k["AttributeName"] for k in t["KeySchema"])
        return f"{t['TableName']}  {t['TableStatus']}  {t['BillingModeSummary']['BillingMode']}  keys={keys}  items~{t['ItemCount']}"

    def function() -> str:
        f = s.client("lambda").get_function(FunctionName="handoff-tick")["Configuration"]
        return f"{f['FunctionName']}  {f['Runtime']}  {f['State']}"

    checks = [
        ("IAM identity", lambda: s.client("sts").get_caller_identity()["Arn"]),
        ("AgentCore Runtime", lambda: ", ".join(f"{r['agentRuntimeName']} {r['status']}" for r in control.list_agent_runtimes()["agentRuntimes"])),
        ("AgentCore Memory", lambda: ", ".join(f"{m['id']} {m['status']}" for m in control.list_memories()["memories"])),
        ("DynamoDB", table),
        ("Lambda", function),
        ("EventBridge Scheduler", lambda: ", ".join(f"{x['Name']} {x['State']}" for x in s.client("scheduler").list_schedules(NamePrefix="handoff")["Schedules"])),
        ("ECR", lambda: ", ".join(f"{r['repositoryName']} ({len(s.client('ecr').list_images(repositoryName=r['repositoryName'])['imageIds'])} images)" for r in s.client("ecr").describe_repositories(repositoryNames=["handoff"])["repositories"])),
        ("Bedrock (Nova profiles)", lambda: ", ".join(sorted(p["inferenceProfileId"] for p in s.client("bedrock").list_inference_profiles()["inferenceProfileSummaries"] if "nova" in p["inferenceProfileId"]))),
        ("Polly neural voices", lambda: f"{len(s.client('polly').describe_voices(Engine='neural', LanguageCode='en-US')['Voices'])} en-US voices"),
        ("IAM roles", lambda: ", ".join(r["RoleName"] for r in boto3.client("iam").list_roles()["Roles"] if r["RoleName"].lower().startswith("handoff"))),
    ]
    failed = 0
    for name, fn in checks:
        try:
            print(f"\033[32m✓\033[0m {name:<24} {mask(fn())}")
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            failed += 1
            print(f"\033[31m✗\033[0m {name:<24} {type(exc).__name__}: {mask(str(exc))[:140]}")
    print(f"\n{len(checks) - failed}/{len(checks)} live in {REGION} · {datetime.datetime.now():%Y-%m-%d %H:%M}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
