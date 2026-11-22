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


class RootClosureTests(unittest.TestCase):
    def test_closure_names_the_real_main_scene(self) -> None:
        required, absent = ev.read_closure()
        self.assertIn("scenes/Main.tscn", required)
        self.assertIn("scripts/autoload/GameData.gd", required)
        self.assertIn("scripts/Walker.gd", required)
        self.assertIn("scripts/Footprints.gd", required)
        self.assertIn("scripts/GardenLoader.gd", required)
        self.assertIn("icon.png", required)
        self.assertIn("art/garden3d/H1/interior/meshes/door.png", absent)
        self.assertNotIn("export_presets.cfg", required)

    def test_windows_import_log_is_fatal(self) -> None:
        text = Path("/home/ubuntu/.cursor/projects/agent-repos-manakhemia/uploads/root.import.err_9153.log").read_text(encoding="utf-8")
        report = ev.classify_godot_log(text, set(ev.read_closure()[0]))
        self.assertTrue(report["fatal"])
        self.assertTrue(any("Main.tscn" in line for line in report["fatal"]))
        self.assertTrue(any("GameData.gd" in line for line in report["fatal"]))

    def test_four_renderer_material_lines_are_teardown(self) -> None:
        text = Path("/home/ubuntu/.cursor/projects/agent-repos-manakhemia/uploads/pilot.err_9863.log").read_text(encoding="utf-8")
        report = ev.classify_godot_log(text, set(ev.read_closure()[0]))
        self.assertEqual(len(report["material_null"]), 4)
        self.assertEqual(report["material_null_class"], "lifetime_cleanup")
        self.assertFalse(report["fatal"])
        for name in ev.MATERIAL_NULL_FUNCS:
            self.assertIn(name, text)

    def test_json_parse_blocks_and_door_stays_optional(self) -> None:
        text = (
            "ERROR: Parse JSON failed. Error at line 0: Unknown error getting token\n"
            "ERROR: GardenLoader: missing JSON res://art/garden3d/H1/interior/objects.json\n"
            "ERROR: Resource file not found: res://art/garden3d/H1/interior/meshes/door.png\n"
        )
        report = ev.classify_godot_log(text, set(ev.read_closure()[0]))
        self.assertTrue(any("Parse JSON" in line for line in report["fatal"]))
        self.assertTrue(any("missing JSON" in line for line in report["fatal"]))
        self.assertTrue(report["baseline_known_optional"])
        self.assertFalse(any("door.png" in line for line in report["fatal"]))

    def test_known_absent_door_texture_is_not_an_import_stop(self) -> None:
        text = "ERROR: Resource file not found: res://art/garden3d/H1/interior/meshes/door.png\n"
        report = ev.classify_godot_log(text, set(ev.read_closure()[0]))
        self.assertFalse(report["fatal"])

    def test_art_only_baseline_fails_before_a_work_tree_is_written(self) -> None:
        repo = Path("/agent/repos/manakhemia")
        base = self._art_only(minimal=True)
        delta = self.tmp / "delta.zip"
        _zip(delta, _package({"tools/hd2d_delta_marker.txt": b"marker"}))
        work = self.tmp / "work"
        with self.assertRaises(SystemExit) as caught:
            ev.prepare(base, delta, work, root_packs=[])
        self.assertIn("scenes/Main.tscn", str(caught.exception.code))
        self.assertFalse(work.exists())

    def test_support_pack_without_assets_fails_before_write(self) -> None:
        repo = Path("/agent/repos/manakhemia")
        required, _absent = ev.read_closure()
        support, _assets = ev.split_closure(required)
        pack = self.tmp / "support.zip"
        ev.build_support_zip(repo, pack, support)
        base = self._art_only(minimal=True)
        delta = self.tmp / "delta.zip"
        _zip(delta, _package({"tools/hd2d_delta_marker.txt": b"marker"}))
        work = self.tmp / "work"
        with self.assertRaises(SystemExit) as caught:
            ev.prepare(base, delta, work, root_packs=[pack])
        self.assertIn("missing the root game files", str(caught.exception.code))
        self.assertNotIn("scenes/Main.tscn", str(caught.exception.code))
        self.assertFalse(work.exists())

    def test_art_only_plus_both_packs_rebuilds_the_root(self) -> None:
        repo = Path("/agent/repos/manakhemia")
        required, _absent = ev.read_closure()
        support, assets = ev.split_closure(required)
        support_zip = self.tmp / "support.zip"
        assets_zip = self.tmp / "assets.zip"
        ev.build_support_zip(repo, support_zip, support)
        ev.build_support_zip(repo, assets_zip, assets)
        base = self._art_only(minimal=False)
        preset = base / "export_presets.cfg"
        preset.write_bytes(b"SECRET")
        preset.chmod(0)
        delta = self.tmp / "delta.zip"
        _zip(delta, _package({"tools/hd2d_delta_marker.txt": b"marker"}))
        work = self.tmp / "work"
        pilot = self.tmp / "pilot"
        try:
            ev.prepare(base, delta, work, root_packs=[support_zip, assets_zip])
            ev.make_pilot(work, pilot)
        finally:
            preset.chmod(stat.S_IRUSR | stat.S_IWUSR)
        self.assertEqual((work / "scenes/Main.tscn").read_bytes(), (repo / "scenes/Main.tscn").read_bytes())
        self.assertTrue((work / "scripts/autoload/SaveSystem.gd").is_file())
        self.assertTrue((work / "addons/beehave/plugin.cfg").is_file())
        self.assertTrue((work / "icon.png").is_file())
        self.assertFalse((work / "export_presets.cfg").exists())
        self.assertIn("viewport_height=2280", (pilot / "project.godot").read_text(encoding="utf-8"))
        self.assertIn("viewport_height=1920", (base / "godot_hd2d_v6/project.godot").read_text(encoding="utf-8"))

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="hd2d_root_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def _art_only(self, minimal: bool) -> Path:
        repo = Path("/agent/repos/manakhemia")
        base = self.tmp / "art_only"
        base.mkdir()
        names = []
        for manifest in ("hd2d_baseline_67519344.sha256", "hd2d_stage_prerequisites.sha256"):
            for _digest, rel in ev.read_manifest(repo / "tools" / manifest):
                names.append(rel)
        if not minimal:
            source = repo / "godot_hd2d_v6"
            for src in source.rglob("*"):
                if not src.is_file() or src.is_symlink() or ev.skipped(src):
                    continue
                rel = "godot_hd2d_v6/" + src.relative_to(source).as_posix()
                names.append(rel)
        for rel in sorted(set(names)):
            src = repo / rel
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            __import__("shutil").copyfile(src, dest)
        return base


if __name__ == "__main__":
    unittest.main()
