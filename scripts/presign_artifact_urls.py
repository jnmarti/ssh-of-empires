#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys


def presign(bucket: str, key: str, region: str, expires_in: str) -> str:
    command = [
        "aws",
        "s3",
        "presign",
        f"s3://{bucket}/{key}",
        "--region",
        region,
        "--expires-in",
        expires_in,
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main() -> int:
    query = json.load(sys.stdin)
    bucket = query["bucket"]
    region = query["region"]
    expires_in = query["expires_in"]
    output = {
        "game_url": presign(bucket, query["game_key"], region, expires_in),
        "site_url": presign(bucket, query["site_key"], region, expires_in),
        "ssh_host_private_url": presign(bucket, query["ssh_host_private_key"], region, expires_in),
        "ssh_host_public_url": presign(bucket, query["ssh_host_public_key"], region, expires_in),
    }
    json.dump(output, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
