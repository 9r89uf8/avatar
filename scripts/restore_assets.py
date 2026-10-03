"""Restore byte-identical delivery assets using only the Python standard library.

Run from any directory. Optional paths are repository-relative manifest targets.
Without config/delivery-parts.json this is a no-op for older standalone packages.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "config/delivery-parts.json"
BLOCK_SIZE = 1024 * 1024


def contained_path(root, name):
    """Require portable relative paths and reject symlinks, including parents."""
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or "\0" in name or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ValueError(f"Unsafe repository-relative path: {name!r}")
    path = root
    for component in name.split("/"):
        path = path / component
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in delivery paths: {name}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes repository: {name}")
    return path


def load_manifest(root):
    path = contained_path(root, MANIFEST)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or type(data.get("schemaVersion")) is not int
            or data["schemaVersion"] != 1 or not isinstance(data.get("assets"), list)):
        raise ValueError("Unsupported delivery-parts manifest; expected schemaVersion 1")
    assets = {}
    records = {}

    def validate(record):
        if not isinstance(record, dict):
            raise ValueError("Each asset and part must be an object")
        contained_path(root, record.get("path"))
        if (type(record.get("bytes")) is not int or not 0 <= record["bytes"] <= 2**53 - 1
                or not isinstance(record.get("sha256"), str)
                or re.fullmatch(r"[a-f0-9]{64}", record["sha256"]) is None):
            raise ValueError(f"Invalid byte count or SHA-256 for {record['path']}")
        signature = (record["bytes"], record["sha256"])
        if record["path"] in records and records[record["path"]] != signature:
            raise ValueError(f"Conflicting metadata for {record['path']}")
        records[record["path"]] = signature

    for asset in data["assets"]:
        validate(asset)
        if asset["path"] == MANIFEST or asset["path"] in assets:
            raise ValueError(f"Duplicate or reserved asset path: {asset['path']}")
        if not isinstance(asset.get("parts"), list) or not asset["parts"]:
            raise ValueError(f"Missing parts for {asset['path']}")
        for part in asset["parts"]:
            validate(part)
        if sum(part["bytes"] for part in asset["parts"]) != asset["bytes"]:
            raise ValueError(f"Part byte counts do not sum to {asset['path']}")
        assets[asset["path"]] = asset

    # Parts may name another complete asset; validate that alias graph up front.
    checked = set()

    def visit(name, active):
        if name in active:
            raise ValueError(f"Cyclic asset parts at {name}")
        if name in checked:
            return
        for part in assets[name]["parts"]:
            if part["path"] in assets:
                visit(part["path"], active | {name})
        checked.add(name)

    for name in assets:
        visit(name, set())
    return assets


def file_blocks(root, record):
    path = contained_path(root, record["path"])
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size != record["bytes"]:
        raise ValueError(f"Missing, incomplete or corrupted file: {record['path']}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size != record["bytes"]:
            raise ValueError(f"Missing, incomplete or corrupted file: {record['path']}")
        yield from iter(lambda: stream.read(BLOCK_SIZE), b"")


def verified_blocks(root, record, assets):
    """Stream and verify each leaf, whole-asset alias, and final combined asset."""
    digest = hashlib.sha256()
    count = 0
    if record["path"] in assets:
        blocks = (block for part in assets[record["path"]]["parts"]
                  for block in verified_blocks(root, part, assets))
    else:
        blocks = file_blocks(root, record)
    for block in blocks:
        digest.update(block)
        count += len(block)
        yield block
    if count != record["bytes"] or digest.hexdigest() != record["sha256"]:
        raise ValueError(f"Byte count or SHA-256 mismatch: {record['path']}")


def existing_matches(root, record):
    path = contained_path(root, record["path"])
    if not path.exists():
        return False
    try:
        digest = hashlib.sha256()
        for block in file_blocks(root, record):
            digest.update(block)
        if digest.hexdigest() == record["sha256"]:
            return True
    except (OSError, ValueError):
        pass
    raise FileExistsError(f"Refusing to overwrite a different existing file: {record['path']}")


def restore_asset(root, asset, assets, verify_only=False):
    target = contained_path(root, asset["path"])
    already_exists = existing_matches(root, asset)
    temporary = None
    output = None
    try:
        if not verify_only and not already_exists:
            target.parent.mkdir(parents=True, exist_ok=True)
            contained_path(root, asset["path"])
            output = tempfile.NamedTemporaryFile(dir=target.parent, prefix=".asset-restore-", delete=False)
            temporary = Path(output.name)
        for block in verified_blocks(root, asset, assets):
            if output is not None:
                output.write(block)
        if output is not None:
            output.flush()
            os.fsync(output.fileno())
            output.close()
            output = None
            contained_path(root, asset["path"])
            try:
                # Same-directory hard-link publication is atomic and cannot replace
                # a file created concurrently. Never use an overwriting rename.
                os.link(temporary, target)
            except FileExistsError:
                existing_matches(root, asset)
                already_exists = True
        status = "Verified" if verify_only else "Already restored and verified" if already_exists else "Restored and verified"
        print(f"{status}: {asset['path']} ({asset['bytes']} bytes; SHA-256 {asset['sha256']})")
    finally:
        if output is not None:
            output.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Verify all parts, combined hashes and any existing target files; write nothing")
    parser.add_argument("paths", nargs="*", help="Optional exact repository-relative asset paths; default: all assets")
    args = parser.parse_args(argv)
    assets = load_manifest(ROOT)
    if assets is None:
        print("No delivery-parts manifest; standalone assets need no restoration.")
        return
    selected = list(dict.fromkeys(args.paths)) if args.paths else list(assets)
    for name in selected:
        if name not in assets:
            raise ValueError(f"Asset is not in the delivery manifest: {name}")
    for name in selected:
        restore_asset(ROOT, assets[name], assets, args.verify_only)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Asset restoration failed: {error}", file=sys.stderr)
        sys.exit(1)
