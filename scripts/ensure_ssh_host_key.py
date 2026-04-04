#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture_output)


def file_exists(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def ensure_public_key(private_path: Path, public_path: Path) -> None:
    result = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(private_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    public_path.write_text(result.stdout, encoding="utf-8")
    os.chmod(public_path, 0o644)


def head_object(bucket: str, key: str, region: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile() as error_file:
        result = subprocess.run(
            [
                "aws",
                "s3api",
                "head-object",
                "--bucket",
                bucket,
                "--key",
                key,
                "--region",
                region,
            ],
            check=False,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=error_file,
        )
        error_file.seek(0)
        error_text = error_file.read().decode("utf-8", errors="replace")
    return result.returncode == 0, error_text


def object_missing(error_text: str) -> bool:
    lowered = error_text.lower()
    return "not found" in lowered or "(404)" in lowered or "404" in lowered


def download_object(bucket: str, key: str, region: str, destination: Path) -> None:
    run(
        [
            "aws",
            "s3",
            "cp",
            f"s3://{bucket}/{key}",
            str(destination),
            "--region",
            region,
            "--only-show-errors",
        ]
    )


def fingerprint(public_path: Path) -> str:
    result = subprocess.run(
        ["ssh-keygen", "-lf", str(public_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    parts = result.stdout.strip().split()
    if len(parts) < 2:
        raise RuntimeError(f"unexpected ssh-keygen output: {result.stdout!r}")
    return parts[1]


def main() -> int:
    query = json.load(sys.stdin)

    private_path = Path(query["private_key_path"]).expanduser()
    public_path = Path(query["public_key_path"]).expanduser()
    bucket = query["bucket"]
    region = query["region"]
    private_object_key = query["private_key_object_key"]
    public_object_key = query["public_key_object_key"]

    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    if file_exists(private_path):
        os.chmod(private_path, 0o600)
        if not file_exists(public_path):
            ensure_public_key(private_path, public_path)
        output = {
            "private_path": str(private_path),
            "public_path": str(public_path),
            "fingerprint": fingerprint(public_path),
        }
        json.dump(output, sys.stdout)
        return 0

    private_exists, private_error = head_object(bucket, private_object_key, region)
    public_exists, public_error = head_object(bucket, public_object_key, region)

    if private_exists and public_exists:
        download_object(bucket, private_object_key, region, private_path)
        download_object(bucket, public_object_key, region, public_path)
        os.chmod(private_path, 0o600)
        os.chmod(public_path, 0o644)
    elif not private_exists and not public_exists and object_missing(private_error) and object_missing(public_error):
        run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private_path)])
        os.chmod(private_path, 0o600)
        os.chmod(public_path, 0o644)
    else:
        raise RuntimeError(
            "unable to ensure persistent SSH host key; "
            f"private exists={private_exists}, public exists={public_exists}, "
            f"private error={private_error!r}, public error={public_error!r}"
        )

    output = {
        "private_path": str(private_path),
        "public_path": str(public_path),
        "fingerprint": fingerprint(public_path),
    }
    json.dump(output, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
