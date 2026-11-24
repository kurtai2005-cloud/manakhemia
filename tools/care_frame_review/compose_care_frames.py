#!/usr/bin/env python3
"""Bake 64x64 care frames from the frozen 580 radiant atlas.

Body pixels stay where the atlas drew them. Face pieces are stamped so the
piece pivot lands on the CLIPS radiant anchor. The atlas body pivot (32, 61)
is recorded and is not used as the r4 world foot.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATLAS_PNG = ROOT / "art/liveliness/atlas_radiant_live.png"
ATLAS_JSON = ROOT / "art/liveliness/atlas_radiant_live.json"
CLIPS = ROOT / "art/liveliness/CLIPS.json"
R4_IDLE = ROOT / "godot_hd2d_v6/art/pet/r4/pet_tuanrong_radiant_front_idle_01.png"
OUT = Path(__file__).resolve().parent

EXPECTED = {
    ATLAS_PNG: "b7a4a9dc6db5fe09c9089c573add40c154dbf1414ba5c9c67c4cbc79a6dbf20b",
    ATLAS_JSON: "f7e982ee09aa627634c58bfeaaec87ef045f87988588b5c9bfb97f45adc4d608",
    CLIPS: "fd1d72fad8f2aafe34a7907cc3a3b9c960d8b10edcfdee14ecf8d77fd2124801",
}

# Art review: last solid row. Grounded frames stay on 62. Emo lifts stay lifted.
EXPECT_ROW = {
    "idle": 62,
    "eat_01": 62,
    "eat_02": 62,
    "eat_03": 62,
    "eat_04": 62,
    "emo_happy_01": 62,
    "emo_happy_02": 60,
    "emo_surprised_01": 60,
    "emo_surprised_02": 61,
    "nuzzle_01": 62,
    "nuzzle_02": 62,
    "nuzzle_03": 62,
    "nuzzle_04": 62,
    "nuzzle_05": 62,
    "nuzzle_06": 62,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_sources() -> None:
    for path, digest in EXPECTED.items():
        if not path.is_file():
            raise SystemExit(f"missing source {path}")
        got = sha256(path)
        if got != digest:
            raise SystemExit(f"source hash mismatch {path}\n  expected {digest}\n  actual   {got}")


def read_png(path: Path) -> tuple[int, int, bytearray]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"not a png: {path}")
    pos = 8
    width = height = 0
    color = 0
    blob = b""
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, bit, color, comp, filt, inter = struct.unpack(">IIBBBBB", payload)
            if (bit, color, comp, filt, inter) != (8, 6, 0, 0, 0):
                raise SystemExit(f"png is not 8-bit RGBA: {path}")
        elif tag == b"IDAT":
            blob += payload
        elif tag == b"IEND":
            break
        pos += 12 + length
    raw = zlib.decompress(blob)
    stride = width * 4
    rows = bytearray()
    prev = bytearray(stride)
    index = 0
    for _y in range(height):
        filt = raw[index]
        index += 1
        row = bytearray(raw[index:index + stride])
        index += stride
        out = bytearray(stride)
        for x, value in enumerate(row):
            left = out[x - 4] if x >= 4 else 0
            up = prev[x]
            up_left = prev[x - 4] if x >= 4 else 0
            if filt == 0:
                cur = value
            elif filt == 1:
                cur = (value + left) & 255
            elif filt == 2:
                cur = (value + up) & 255
            elif filt == 3:
                cur = (value + ((left + up) // 2)) & 255
            elif filt == 4:
                estimate = left + up - up_left
                pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - up_left)
                pred = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                cur = (value + pred) & 255
            else:
                raise SystemExit(f"bad png filter {filt}")
            out[x] = cur
        rows += out
        prev = out
    return width, height, rows


def write_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def crop(src: bytearray, sw: int, x: int, y: int, w: int, h: int) -> bytearray:
    out = bytearray(w * h * 4)
    for row in range(h):
        start = ((y + row) * sw + x) * 4
        out[row * w * 4:(row + 1) * w * 4] = src[start:start + w * 4]
    return out


def fringe_count(img: bytes) -> int:
    return sum(1 for i in range(3, len(img), 4) if 0 < img[i] < 255)


def last_solid_row(img: bytes, width: int, height: int) -> int:
    last = -1
    for y in range(height):
        row = img[y * width * 4:(y + 1) * width * 4]
        if any(row[i] == 255 for i in range(3, len(row), 4)):
            last = y
    return last


def blit(dst: bytearray, piece: bytes, dx: int, dy: int, pw: int, ph: int) -> None:
    for y in range(ph):
        for x in range(pw):
            src_i = (y * pw + x) * 4
            if piece[src_i + 3] == 0:
                continue
            if piece[src_i + 3] != 255:
                raise SystemExit("face piece has a soft edge; refusing to blend a new fringe")
            px, py = dx + x, dy + y
            if not (0 <= px < 64 and 0 <= py < 64):
                raise SystemExit(f"face piece falls outside the 64 frame at {px},{py}")
            dst_i = (py * 64 + px) * 4
            dst[dst_i:dst_i + 4] = piece[src_i:src_i + 4]


def piece_key(kind: str, style: str, gaze: str, side: str) -> str:
    if kind == "eye":
        if style in ("happy", "sleepy", "wink"):
            gaze = "C"
        return f"eyes_{style}_{gaze}_{side}"
    return f"mouth_{style}"


def place_face(body: bytearray, frames: dict, atlas: bytearray, aw: int, anchor: dict) -> None:
    face = anchor["face"]
    eyes = str(face["eyes"])
    gaze = str(face.get("gaze", "C"))
    mouth = str(face["mouth"])
    kit = {
        "eyeL": ("eye", eyes, gaze, "l", anchor["eyeL"]),
        "eyeR": ("eye", eyes, gaze, "r", anchor["eyeR"]),
        "mouth": ("mouth", mouth, "", "", anchor["mouth"]),
    }
    for _name, (kind, style, gz, side, point) in kit.items():
        key = piece_key(kind, style, gz, side)
        if key not in frames:
            raise SystemExit(f"missing face piece {key}")
        info = frames[key]
        rect = info["frame"]
        pivot = info["pivotPx"]
        if kind == "eye" and (pivot["x"], pivot["y"], rect["w"], rect["h"]) != (4, 4, 9, 8):
            raise SystemExit(f"eye piece {key} is not the radiant 9x8 pivot (4,4)")
        if kind == "mouth" and (pivot["x"], pivot["y"], rect["w"], rect["h"]) != (3, 0, 7, 4):
            raise SystemExit(f"mouth piece {key} is not the radiant 7x4 pivot (3,0)")
        piece = crop(atlas, aw, rect["x"], rect["y"], rect["w"], rect["h"])
        if fringe_count(piece):
            raise SystemExit(f"face piece {key} has partial alpha")
        blit(body, piece, int(point[0]) - int(pivot["x"]), int(point[1]) - int(pivot["y"]), rect["w"], rect["h"])


def _only_face_changed(before: bytes, after: bytes, frames: dict, atlas: bytearray, aw: int, anchor: dict) -> None:
    face = anchor["face"]
    pieces = [
        ("eye", str(face["eyes"]), str(face.get("gaze", "C")), "l", anchor["eyeL"]),
        ("eye", str(face["eyes"]), str(face.get("gaze", "C")), "r", anchor["eyeR"]),
        ("mouth", str(face["mouth"]), "", "", anchor["mouth"]),
    ]
    covered = bytearray(64 * 64)
    for kind, style, gaze, side, point in pieces:
        key = piece_key(kind, style, gaze, side)
        rect = frames[key]["frame"]
        pivot = frames[key]["pivotPx"]
        piece = crop(atlas, aw, rect["x"], rect["y"], rect["w"], rect["h"])
        dx = int(point[0]) - int(pivot["x"])
        dy = int(point[1]) - int(pivot["y"])
        for y in range(rect["h"]):
            for x in range(rect["w"]):
                if piece[(y * rect["w"] + x) * 4 + 3] == 0:
                    continue
                covered[(dy + y) * 64 + (dx + x)] = 1
    for i in range(64 * 64):
        if before[i * 4:(i + 1) * 4] != after[i * 4:(i + 1) * 4] and not covered[i]:
            raise SystemExit("a pixel changed outside the eye and mouth pieces")


def composite(frames: dict, atlas: bytearray, aw: int, clips: dict, clip: str, index: int, frame_name: str) -> bytearray:
    key = f"{frame_name}_noface_{index + 1:02d}" if frame_name != "nuzzle" else f"nuzzle_{index + 1:02d}"
    if frame_name == "idle":
        key = f"idle_noface_{index + 1:02d}"
    info = frames[key]
    rect = info["frame"]
    pivot = info.get("pivotPx")
    if rect["w"] != 64 or rect["h"] != 64:
        raise SystemExit(f"{key} is not 64x64")
    if not pivot or (pivot["x"], pivot["y"]) != (32, 61):
        raise SystemExit(f"{key} pivotPx is not (32, 61)")
    image = crop(atlas, aw, rect["x"], rect["y"], 64, 64)
    if fringe_count(image):
        raise SystemExit(f"{key} has partial alpha")
    if frame_name == "nuzzle":
        return image
    before = bytearray(image)
    anchors = clips[clip]["anchors"]["radiant"]
    place_face(image, frames, atlas, aw, anchors[index])
    _only_face_changed(before, image, frames, atlas, aw, anchors[index])
    if fringe_count(image):
        raise SystemExit(f"composite {clip} {index} gained a soft edge")
    return image


def scale_near(img: bytes, width: int, height: int, factor: int) -> bytearray:
    out_w, out_h = width * factor, height * factor
    out = bytearray(out_w * out_h * 4)
    for y in range(out_h):
        sy = y // factor
        for x in range(out_w):
            sx = x // factor
            s = (sy * width + sx) * 4
            d = (y * out_w + x) * 4
            out[d:d + 4] = img[s:s + 4]
    return out


def put_px(img: bytearray, width: int, x: int, y: int, color: bytes) -> None:
    if 0 <= x < width and 0 <= y < len(img) // (width * 4):
        i = (y * width + x) * 4
        img[i:i + 4] = color


def draw_label(img: bytearray, width: int, x: int, y: int, text: str) -> None:
    # 3x5 glyphs for the sheet labels. Not part of the pet.
    glyphs = {
        "0": ["111", "101", "101", "101", "111"],
        "1": ["010", "110", "010", "010", "111"],
        "2": ["111", "001", "111", "100", "111"],
        "3": ["111", "001", "111", "001", "111"],
        "4": ["101", "101", "111", "001", "001"],
        "5": ["111", "100", "111", "001", "111"],
        "6": ["111", "100", "111", "101", "111"],
        "a": ["111", "101", "111", "101", "101"],
        "d": ["110", "101", "101", "101", "110"],
        "e": ["111", "100", "111", "100", "111"],
        "f": ["111", "100", "110", "100", "100"],
        "h": ["101", "101", "111", "101", "101"],
        "i": ["111", "010", "010", "010", "111"],
        "l": ["100", "100", "100", "100", "111"],
        "n": ["110", "101", "101", "101", "101"],
        "p": ["111", "101", "111", "100", "100"],
        "r": ["110", "101", "110", "101", "101"],
        "s": ["111", "100", "111", "001", "111"],
        "t": ["111", "010", "010", "010", "010"],
        "u": ["101", "101", "101", "101", "111"],
        "z": ["111", "001", "010", "100", "111"],
        " ": ["000", "000", "000", "000", "000"],
        "-": ["000", "000", "111", "000", "000"],
    }
    color = b"\xff\xff\xff\xff"
    cursor = x
    for ch in text:
        glyph = glyphs.get(ch, glyphs[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    put_px(img, width, cursor + gx, y + gy, color)
        cursor += 4


def build_sheet(groups: list[list[tuple[str, bytes]]]) -> tuple[int, int, bytes]:
    scale = 4
    cell = 64 * scale
    gap = 12
    label_h = 10
    margin = 10
    baseline = 63 * scale  # bottom edge of row 62, the r4 sole boundary
    cols = max(len(row) for row in groups)
    width = margin * 2 + cols * cell + (cols - 1) * gap
    height = margin * 2 + len(groups) * (cell + label_h + 8) + (len(groups) - 1) * gap
    img = bytearray(b"\x22\x24\x2a\xff" * (width * height))
    marker = b"\xff\x30\xb0\xff"
    y0 = margin
    for row in groups:
        x0 = margin
        for name, frame in row:
            scaled = scale_near(frame, 64, 64, scale)
            for y in range(cell):
                src = y * cell * 4
                dst = ((y0 + label_h + y) * width + x0) * 4
                img[dst:dst + cell * 4] = scaled[src:src + cell * 4]
            draw_label(img, width, x0, y0, name)
            line_y = y0 + label_h + baseline
            for t in range(3):
                for x in range(x0 - 14, x0 + cell + 8):
                    if x0 <= x < x0 + cell:
                        continue
                    put_px(img, width, x, line_y + t - 1, marker)
            x0 += cell + gap
        y0 += cell + label_h + 8 + gap
    return width, height, bytes(img)


def load_clips() -> dict:
    doc = json.loads(CLIPS.read_text(encoding="utf-8"))
    found = {}
    for clip in doc["clips"]:
        if clip.get("name") in ("idle", "eat", "emo_happy", "emo_surprised", "nuzzle"):
            if "pivot" in clip or "pivotPx" in clip:
                raise SystemExit(f"CLIPS clip {clip['name']} unexpectedly carries a pivot")
            found[clip["name"]] = clip
    return found


def bake() -> dict:
    require_sources()
    aw, ah, atlas = read_png(ATLAS_PNG)
    if (aw, ah) != (1024, 1024):
        raise SystemExit("atlas is not 1024x1024")
    frames = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))["frames"]
    clips = load_clips()
    rw, rh, r4 = read_png(R4_IDLE)
    if (rw, rh) != (64, 64):
        raise SystemExit("r4 idle is not 64x64")
    idle = composite(frames, atlas, aw, clips, "idle", 0, "idle")
    diff = sum(1 for a, b in zip(idle, r4) if a != b)
    if diff:
        raise SystemExit(f"composited idle is not pixel-identical to r4 idle: {diff} bytes differ")
    made = {"idle": idle, "r4_idle": bytearray(r4)}
    jobs = [
        ("eat", "eat", 4),
        ("emo_happy", "emo_happy", 2),
        ("emo_surprised", "emo_surprised", 2),
        ("nuzzle", "nuzzle", 6),
    ]
    rows = {"idle": last_solid_row(idle, 64, 64)}
    for clip, stem, count in jobs:
        for index in range(count):
            name = f"{stem}_{index + 1:02d}"
            image = composite(frames, atlas, aw, clips, clip, index, stem)
            made[name] = image
            rows[name] = last_solid_row(image, 64, 64)
            if rows[name] != EXPECT_ROW[name]:
                raise SystemExit(f"{name} last solid row is {rows[name]}, review expects {EXPECT_ROW[name]}")
    if rows["idle"] != 62:
        raise SystemExit(f"idle last solid row is {rows['idle']}")
    report = {
        "idle_equals_r4": True,
        "idle_diff_bytes": 0,
        "body_pivot_px_recorded": [32, 61],
        "body_pivot_used_as_world_foot": False,
        "foot_rule": "64 quad, node y=29, offset.y=2, pixel_size=1, image boundary 63 (row 62) at world y=0",
        "emo_lifts_retained": True,
        "last_solid_row": rows,
        "bulb_overlaid": False,
        "nuzzle_source": "full-faced nuzzle_01..06, not a face-kit composite",
        "renderer": "cpu nearest composite, not a Mobile screenshot",
        "rights": "unverified",
    }
    return {"frames": made, "report": report}


def write_outputs(baked: dict) -> None:
    frames: dict[str, bytearray] = baked["frames"]
    frame_dir = OUT / "frames"
    for name, image in frames.items():
        if name == "r4_idle":
            continue
        write_png(frame_dir / f"{name}.png", 64, 64, image)
    write_png(frame_dir / "r4_front_idle_reference.png", 64, 64, frames["r4_idle"])
    groups = [
        [("idle", frames["idle"]), ("r4idle", frames["r4_idle"]), ("diff0", bytearray(b"\x00\x00\x00\x00" * (64 * 64)))],
        [("eat1", frames["eat_01"]), ("eat2", frames["eat_02"]), ("eat3", frames["eat_03"]), ("eat4", frames["eat_04"]), ("idle", frames["idle"])],
        [("hap1", frames["emo_happy_01"]), ("hap2", frames["emo_happy_02"]), ("idle", frames["idle"])],
        [("sur1", frames["emo_surprised_01"]), ("sur2", frames["emo_surprised_02"]), ("idle", frames["idle"])],
        [("nuz" + str(i), frames[f"nuzzle_{i:02d}"]) for i in range(1, 7)],
    ]
    # The third cell of row 0 is a real diff, not a blank.
    diff = bytearray(b"\x00\x00\x00\xff" * (64 * 64))
    groups[0][2] = ("diff0", diff)
    sw, sh, sheet = build_sheet(groups)
    write_png(OUT / "sheets" / "care_contact_nearest.png", sw, sh, sheet)
    (OUT / "compose_report.json").write_text(json.dumps(baked["report"], indent=2) + "\n", encoding="utf-8")


def main() -> None:
    baked = bake()
    if "--write" in sys.argv:
        write_outputs(baked)
        print("wrote care frames; idle diff 0; not a Mobile screenshot")
    else:
        print(json.dumps(baked["report"], indent=2))


if __name__ == "__main__":
    main()
