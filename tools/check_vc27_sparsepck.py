#!/usr/bin/env python3
"""Keep Godot's sparse pack index equal to the files inside the APK."""
import hashlib
import struct
import sys
import zipfile
from pathlib import Path

PACK_FILE_REMOVAL = 1 << 1


def parse_sparsepck(data: bytes) -> list[dict]:
    if data[:4] != b"GDPC":
        raise SystemExit("sparsepck magic")
    version = struct.unpack_from("<I", data, 4)[0]
    flags = struct.unpack_from("<I", data, 20)[0]
    if version < 3:
        raise SystemExit("sparsepck version %s" % version)
    if flags & 1:
        raise SystemExit("encrypted sparsepck directory")
    dir_offset = struct.unpack_from("<Q", data, 32)[0]
    off = dir_offset
    count = struct.unpack_from("<I", data, off)[0]
    off += 4
    entries = []
    for _ in range(count):
        sl = struct.unpack_from("<I", data, off)[0]
        off += 4
        raw = data[off : off + sl]
        off += sl
        path = raw.rstrip(b"\x00").decode("utf-8")
        size_off = off + 8
        size = struct.unpack_from("<Q", data, size_off)[0]
        off += 16
        md5_off = off
        md5 = bytes(data[off : off + 16])
        off += 16
        file_flags = struct.unpack_from("<I", data, off)[0]
        off += 4
        entries.append(
            {
                "path": path,
                "size": size,
                "size_off": size_off,
                "md5": md5,
                "md5_off": md5_off,
                "flags": file_flags,
            }
        )
    return entries


def sync_assets(assets_dir: Path) -> int:
    pack_path = assets_dir / "assets.sparsepck"
    blob = bytearray(pack_path.read_bytes())
    changed = 0
    for entry in parse_sparsepck(blob):
        if entry["flags"] & PACK_FILE_REMOVAL:
            continue
        file_path = assets_dir / entry["path"]
        if not file_path.is_file():
            continue
        raw = file_path.read_bytes()
        digest = hashlib.md5(raw).digest()
        if entry["size"] == len(raw) and entry["md5"] == digest:
            continue
        struct.pack_into("<Q", blob, entry["size_off"], len(raw))
        blob[entry["md5_off"] : entry["md5_off"] + 16] = digest
        changed += 1
        print("SPARSEPCK_SYNC", entry["path"], entry["size"], len(raw))
    if changed:
        pack_path.write_bytes(blob)
    print("SPARSEPCK_SYNCED", changed, pack_path)
    return changed


def verify_apk(apk_path: Path) -> int:
    with zipfile.ZipFile(apk_path) as zf:
        pack = zf.read("assets/assets.sparsepck")
        entries = parse_sparsepck(pack)
        names = set(zf.namelist())
        mismatch = 0
        project_size = 0
        project_md5 = ""
        for entry in entries:
            if entry["flags"] & PACK_FILE_REMOVAL:
                continue
            apk_name = "assets/" + entry["path"]
            if apk_name not in names:
                mismatch += 1
                print("SPARSEPCK_MISSING_FILE", apk_name)
                continue
            raw = zf.read(apk_name)
            digest = hashlib.md5(raw).hexdigest()
            if entry["path"] == "project.binary":
                project_size = len(raw)
                project_md5 = digest
            if entry["size"] != len(raw) or entry["md5"].hex() != digest:
                mismatch += 1
                print(
                    "SPARSEPCK_BAD",
                    entry["path"],
                    "recorded",
                    entry["size"],
                    entry["md5"].hex(),
                    "actual",
                    len(raw),
                    digest,
                )
    print("SPARSEPCK_ENTRIES=%d" % len(entries))
    print("SPARSEPCK_MISMATCH=%d" % mismatch)
    print("PROJECT_BINARY_SIZE=%d" % project_size)
    print("PROJECT_BINARY_MD5=%s" % project_md5)
    return 1 if mismatch else 0


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: check_vc27_sparsepck.py sync <assets-dir> | verify <apk>", file=sys.stderr)
        return 2
    cmd, target = sys.argv[1], Path(sys.argv[2])
    if cmd == "sync":
        sync_assets(target)
        return 0
    if cmd == "verify":
        return verify_apk(target)
    print("unknown", cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
