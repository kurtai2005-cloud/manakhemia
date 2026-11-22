"""Stdlib checks for delta member integrity and a fresh evidence directory."""
from __future__ import annotations

import hashlib
import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

import hd2d_evidence as ev


def _package(files: dict[str, bytes]) -> dict[str, bytes]:
    rows = []
    for name in sorted(files):
        digest = hashlib.sha256(files[name]).hexdigest()
        rows.append(f"{digest}  {name}")
    packed = dict(files)
    packed[ev.MEMBER_NAME] = ("\n".join(rows) + "\n").encode("utf-8")
    return packed


def _zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as handle:
        for name, data in members.items():
            handle.writestr(name, data)


class DeltaMemberTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="hd2d_delta_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def test_member_hash_accepts_a_complete_list(self) -> None:
        path = self.tmp / "good.zip"
        _zip(path, _package({"keep.txt": b"ordinary"}))
        names = ev.verify_delta_members(path, identity={})
        self.assertEqual(names, ["keep.txt"])
        work = self.tmp / "work"
        work.mkdir()
        ev.apply_delta(path, work, names, identity={})
        self.assertEqual((work / "keep.txt").read_bytes(), b"ordinary")
        self.assertFalse((work / ev.MEMBER_NAME).exists())

    def test_tamper_is_rejected_before_extract(self) -> None:
        packed = _package({"keep.txt": b"ordinary"})
        packed["keep.txt"] = b"tampered"
        path = self.tmp / "tamper.zip"
        _zip(path, packed)
        work = self.tmp / "work"
        work.mkdir()
        (work / "sentinel.txt").write_text("stay", encoding="utf-8")
        with self.assertRaises(SystemExit) as caught:
            ev.apply_delta(path, work, identity={})
        self.assertIn("member hash mismatch", str(caught.exception.code))
        self.assertEqual((work / "sentinel.txt").read_text(encoding="utf-8"), "stay")
        self.assertFalse((work / "keep.txt").exists())

    def test_missing_member_is_rejected(self) -> None:
        packed = _package({"keep.txt": b"ordinary"})
        extra = f"{'ab' * 32}  ghost.txt\n"
        packed[ev.MEMBER_NAME] += extra.encode("utf-8")
        path = self.tmp / "missing.zip"
        _zip(path, packed)
        with self.assertRaises(SystemExit) as caught:
            ev.verify_delta_members(path, identity={})
        self.assertIn("not in the zip", str(caught.exception.code))

    def test_unlisted_member_is_rejected(self) -> None:
        packed = _package({"keep.txt": b"ordinary"})
        packed["extra.txt"] = b"extra"
        path = self.tmp / "unlisted.zip"
        _zip(path, packed)
        with self.assertRaises(SystemExit) as caught:
            ev.verify_delta_members(path, identity={})
        self.assertIn("not listed", str(caught.exception.code))

    def test_duplicate_entry_is_rejected_before_read(self) -> None:
        path = self.tmp / "dup.zip"
        with zipfile.ZipFile(path, "w") as handle:
            handle.writestr("keep.txt", b"one")
        with zipfile.ZipFile(path, "a") as handle:
            handle.writestr("keep.txt", b"two")
            handle.writestr(ev.MEMBER_NAME, b"placeholder\n")
        reads: list[str] = []
        original = zipfile.ZipFile.read

        def spy(zf, name, pwd=None):
            reads.append(str(name))
            return original(zf, name, pwd)

        zipfile.ZipFile.read = spy
        try:
            with self.assertRaises(SystemExit) as caught:
                ev.verify_delta_members(path, identity={})
        finally:
            zipfile.ZipFile.read = original
        self.assertIn("duplicate", str(caught.exception.code))
        self.assertEqual(reads, [])

    def test_duplicate_manifest_row_is_rejected(self) -> None:
        body = b"ordinary"
        digest = hashlib.sha256(body).hexdigest()
        packed = {"keep.txt": body, ev.MEMBER_NAME: f"{digest}  keep.txt\n{digest}  keep.txt\n".encode()}
        path = self.tmp / "dup-manifest.zip"
        _zip(path, packed)
        with self.assertRaises(SystemExit) as caught:
            ev.verify_delta_members(path, identity={})
        self.assertIn("duplicate manifest", str(caught.exception.code))

    def test_secret_entry_is_not_read(self) -> None:
        path = self.tmp / "secret.zip"
        with zipfile.ZipFile(path, "w") as handle:
            handle.writestr("export_presets.cfg", b"SECRET")
            handle.writestr("keep.txt", b"ordinary")
        reads: list[str] = []
        original = zipfile.ZipFile.read

        def spy(zf, name, pwd=None):
            reads.append(str(name))
            if Path(str(name)).name == "export_presets.cfg":
                raise AssertionError("secret entry was read")
            return original(zf, name, pwd)

        zipfile.ZipFile.read = spy
        try:
            with self.assertRaises(SystemExit) as caught:
                ev.verify_delta_members(path, identity={})
        finally:
            zipfile.ZipFile.read = original
        self.assertIn("secret", str(caught.exception.code))
        self.assertEqual(reads, [])

    def test_directory_secret_is_not_opened(self) -> None:
        delta = self.tmp / "dir"
        delta.mkdir()
        secret = delta / "release.keystore"
        secret.write_bytes(b"SECRET")
        secret.chmod(0)
        try:
            with self.assertRaises(SystemExit) as caught:
                ev.verify_delta_members(delta, identity={})
            self.assertIn("secret", str(caught.exception.code))
        finally:
            secret.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_traversal_is_rejected_before_extract(self) -> None:
        outside = self.tmp / "escape.txt"
        path = self.tmp / "slip.zip"
        with zipfile.ZipFile(path, "w") as handle:
            handle.writestr("../escape.txt", b"nope")
        with self.assertRaises(SystemExit) as caught:
            ev.verify_delta_members(path, identity={})
        self.assertIn("refusing delta path", str(caught.exception.code))
        self.assertFalse(outside.exists())

    def test_self_manifest_is_excluded(self) -> None:
        body = b"ordinary"
        digest = hashlib.sha256(body).hexdigest()
        manifest = f"{digest}  keep.txt\n{'cd' * 32}  {ev.MEMBER_NAME}\n".encode()
        path = self.tmp / "self.zip"
        _zip(path, {"keep.txt": body, ev.MEMBER_NAME: manifest})
        with self.assertRaises(SystemExit) as caught:
            ev.verify_delta_members(path, identity={})
        self.assertIn("must not list itself", str(caught.exception.code))

    def test_optional_delta_sha(self) -> None:
        path = self.tmp / "sha.zip"
        _zip(path, _package({"keep.txt": b"ordinary"}))
        digest = ev.sha256(path)
        self.assertEqual(ev.verify_delta_members(path, digest, identity={}), ["keep.txt"])
        with self.assertRaises(SystemExit) as caught:
            ev.verify_delta_members(path, "0" * 64, identity={})
        self.assertIn("delta sha", str(caught.exception.code))

    def test_frozen_hash_is_protected_before_extract(self) -> None:
        rel = "godot_hd2d_v6/scenes/capture.gd"
        path = self.tmp / "frozen.zip"
        _zip(path, _package({rel: b"not the frozen script\n"}))
        work = self.tmp / "work"
        with self.assertRaises(SystemExit) as caught:
            ev.apply_delta(path, work)
        self.assertIn("frozen", str(caught.exception.code))
        self.assertFalse(work.exists())


class OutputEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="hd2d_out_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def test_nonempty_output_is_rejected_without_deletion(self) -> None:
        out = self.tmp / "out"
        out.mkdir()
        stale = out / "root_presentation.png"
        stale.write_bytes(b"stale-png")
        with self.assertRaises(SystemExit) as caught:
            ev.require_fresh_output(out)
        self.assertIn("not empty", str(caught.exception.code))
        self.assertEqual(stale.read_bytes(), b"stale-png")
        ev.require_fresh_output(self.tmp / "missing")
        empty = self.tmp / "empty"
        empty.mkdir()
        ev.require_fresh_output(empty)

    def test_incomplete_capture_fails(self) -> None:
        out = self.tmp / "partial"
        out.mkdir()
        ev.write_png(out / "pilot_standalone.png", 1080, 2280)
        (out / "pilot_standalone.json").write_text(json.dumps(ev.matched_state("pilot_standalone")), encoding="utf-8")
        with self.assertRaises(SystemExit):
            ev.check(out, None)
        self.assertFalse((out / "root_presentation.png").exists())

    def test_stale_png_does_not_pass_a_failed_capture(self) -> None:
        out = self.tmp / "stale"
        out.mkdir()
        ev.write_png(out / "pilot_standalone.png", 1080, 2280)
        ev.write_png(out / "root_presentation.png", 1080, 2280)
        before = (out / "root_presentation.png").read_bytes()
        failed = ev.matched_state("pilot_standalone")
        failed["png_written"] = False
        (out / "pilot_standalone.json").write_text(json.dumps(failed), encoding="utf-8")
        (out / "root_presentation.json").write_text(json.dumps(failed), encoding="utf-8")
        with self.assertRaises(SystemExit) as caught:
            ev.check(out, None)
        self.assertEqual(caught.exception.code, 1)
        result = json.loads((out / "result.json").read_text(encoding="utf-8"))
        self.assertFalse(result["ok"])
        self.assertIn("png_written is false", result["reasons"])
        self.assertFalse(result["windows_gpu_proof"])
        self.assertEqual((out / "root_presentation.png").read_bytes(), before)
        with self.assertRaises(SystemExit):
            ev.require_fresh_output(out)
        self.assertEqual((out / "root_presentation.png").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
