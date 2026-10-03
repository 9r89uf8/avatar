"""Focused delivery-restoration tests: python scripts/test_restore_assets.py."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("restore_assets.py")
TARGET = "web/public/assets/avatar.glb"
SECOND = "exports/avatar-uncompressed.glb"
PAYLOAD = b"exact source bytes\0\xff" * 100


def record(path, data):
    return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class RestoreAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        shutil.copyfile(SCRIPT, self.root / "scripts/restore_assets.py")
        self.parts = []
        for number, data in enumerate((PAYLOAD[:713], PAYLOAD[713:]), 1):
            name = f"delivery/parts/test/part-{number:03}.bin"
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            self.parts.append(record(name, data))
        self.manifest = {"schemaVersion": 1, "assets": [
            {**record(TARGET, PAYLOAD), "parts": self.parts},
            {**record(SECOND, PAYLOAD), "parts": self.parts},
        ]}
        self.save_manifest()

    def save_manifest(self):
        path = self.root / "config/delivery-parts.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_script(self, *args, success=True):
        result = subprocess.run([sys.executable, str(self.root / "scripts/restore_assets.py"), *args],
                                cwd=self.root.parent, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(list(self.root.rglob(".asset-restore-*")), [], "temporary output was cleaned up")
        return result

    def write_target(self, data=PAYLOAD):
        path = self.root / TARGET
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_restores_all_shared_part_targets_exactly_and_repeats_safely(self):
        self.run_script()
        self.assertEqual((self.root / TARGET).read_bytes(), PAYLOAD)
        self.assertEqual((self.root / SECOND).read_bytes(), PAYLOAD)
        self.assertIn("Already restored and verified", self.run_script().stdout)

    def test_selected_alias_streams_without_writing_unselected_dependency(self):
        self.manifest["assets"][1]["parts"] = [record(TARGET, PAYLOAD)]
        self.save_manifest()
        self.run_script(SECOND)
        self.assertEqual((self.root / SECOND).read_bytes(), PAYLOAD)
        self.assertFalse((self.root / TARGET).exists())

    def test_verify_only_writes_nothing(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        self.assertIn("Verified", self.run_script("--verify-only").stdout)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))

    def test_corrupt_part_prevents_publication_and_checks_already_restored(self):
        part = self.root / self.parts[0]["path"]
        part.write_bytes(b"x" * self.parts[0]["bytes"])
        self.assertIn("SHA-256 mismatch", self.run_script(TARGET, success=False).stderr)
        self.assertFalse((self.root / TARGET).exists())
        target = self.write_target()
        self.run_script(TARGET, success=False)
        self.assertEqual(target.read_bytes(), PAYLOAD)

    def test_combined_hash_is_checked_even_when_each_part_matches(self):
        self.manifest["assets"][0]["sha256"] = "0" * 64
        self.save_manifest()
        self.assertIn("SHA-256 mismatch", self.run_script(TARGET, success=False).stderr)
        self.assertFalse((self.root / TARGET).exists())

    def test_different_existing_target_is_never_overwritten(self):
        target = self.write_target(b"my edited source")
        self.assertIn("Refusing to overwrite", self.run_script(TARGET, success=False).stderr)
        self.run_script("--verify-only", TARGET, success=False)
        self.assertEqual(target.read_bytes(), b"my edited source")

    def test_missing_part_prevents_publication(self):
        (self.root / self.parts[1]["path"]).unlink()
        self.run_script(TARGET, success=False)
        self.assertFalse((self.root / TARGET).exists())

    def test_missing_manifest_is_a_safe_standalone_noop(self):
        (self.root / "config/delivery-parts.json").unlink()
        target = self.write_target(b"standalone GLB")
        self.assertIn("No delivery-parts manifest", self.run_script().stdout)
        self.assertEqual(target.read_bytes(), b"standalone GLB")

    def test_unsafe_manifest_paths_are_rejected(self):
        for name in ("../escape", "/tmp/escape", "C:/escape", "a\\escape", "a/../escape"):
            with self.subTest(name=name):
                self.manifest["assets"][0]["path"] = name
                self.save_manifest()
                self.assertIn("Unsafe repository-relative", self.run_script(success=False).stderr)

    def test_symlinked_part_and_target_parent_are_rejected(self):
        part = self.root / self.parts[0]["path"]
        original = part.read_bytes()
        part.unlink()
        outside = self.root / "original.bin"
        outside.write_bytes(original)
        part.symlink_to(outside)
        self.assertIn("Symlinks", self.run_script(TARGET, success=False).stderr)
        part.unlink()
        part.write_bytes(original)
        (self.root / "elsewhere").mkdir()
        (self.root / "web").symlink_to(self.root / "elsewhere", target_is_directory=True)
        self.assertIn("Symlinks", self.run_script(TARGET, success=False).stderr)
        self.assertEqual(list((self.root / "elsewhere").iterdir()), [])

    def test_invalid_selection_conflicts_and_cycles_fail_before_writing(self):
        self.assertIn("not in the delivery manifest", self.run_script(TARGET, "missing.bin", success=False).stderr)
        self.assertFalse((self.root / TARGET).exists())
        self.manifest["assets"][1]["parts"] = [record(TARGET, PAYLOAD)]
        self.manifest["assets"][0]["sha256"] = "0" * 64
        self.save_manifest()
        self.assertIn("Conflicting metadata", self.run_script(success=False).stderr)
        self.manifest["assets"][0] = {**record(TARGET, PAYLOAD), "parts": [record(SECOND, PAYLOAD)]}
        self.save_manifest()
        self.assertIn("Cyclic asset parts", self.run_script(success=False).stderr)

    def test_concurrent_different_file_survives_atomic_publication(self):
        spec = importlib.util.spec_from_file_location("restore_assets", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assets = module.load_manifest(self.root)
        original_link = module.os.link

        def concurrent_link(source, target):
            target.write_bytes(b"concurrent user edit")
            return original_link(source, target)

        with patch.object(module.os, "link", concurrent_link):
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                module.restore_asset(self.root, assets[TARGET], assets)
        self.assertEqual((self.root / TARGET).read_bytes(), b"concurrent user edit")
        self.assertEqual(list(self.root.rglob(".asset-restore-*")), [])


if __name__ == "__main__":
    unittest.main()
