#!/usr/bin/env python3
"""Prepare non-activating DAX3 speaker candidates.

Upstream arithmetic is loaded only from hash-verified source, never its CLI.
Diagnostics are allowlisted. Published ASUS inputs are usable directly;
preparation never reads a live audio session or raw host captures.
"""

import argparse
import contextlib
import hashlib
import importlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SOURCE_MANIFEST = ROOT / "evidence/audio-speaker-sources.json"
INVENTORY = ROOT / "evidence/audio-inventory-2026-10-12.json"
MAX_BYTES = 2 * 1024 * 1024
MAX_NODES = 10000
MAX_DEPTH = 32
ID = re.compile(r"[0-9a-f]{8}\Z")
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
PIN = "430e3a501e21bf8fdb615b133d2e8130b17973c1"
DEVICE_CONTRACTS = {
    ("10ec0285", "10431c63"): {
        "xml_name": "DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml",
        "layout": "front-stereo",
        "bundle_hardware": {"codec": "10ec0285", "subsystem": "10431c63",
                            "amplifiers": "CS35L56", "count": 2, "speaker_id": 0}},
    ("10ec0285", "17aa2276"): {
        "xml_name": "HDAUDIO_DEV_0285_SUBSYS_17AA2276_PCI_SUBSYS_226717AA.xml",
        "layout": "legacy-stereo",
        "source_manifest": "profiles/lenovo/x1-extreme-gen1/manifest.json",
        "bundle_hardware": {"codec": "10ec0285", "subsystem": "17aa2276",
                            "machine_type": "20MF", "pci_subsystem": "17aa2267",
                            "amplifier_identification": "unknown"}}}


class ProfileError(Exception):
    def __init__(self, reason, code=2):
        self.reason, self.code = reason, code


def require(condition, reason, code=2):
    if not condition:
        raise ProfileError(reason, code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def json_load(data):
    try:
        return json.loads(data, object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ProfileError("nonfinite_json")))
    except (ValueError, UnicodeError, RecursionError):
        raise ProfileError("invalid_json") from None


def no_symlinks(path):
    """Reject symlinks in every supplied component, including parent directories."""
    path = Path(os.path.abspath(path))
    require(all(not p.is_symlink() for p in (path, *path.parents)), "symlink_path")
    return path


@contextlib.contextmanager
def parent_fd(path):
    """Walk from root with no-follow directory descriptors, closing race escapes."""
    path = no_symlinks(path)
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY |
                              getattr(os, "O_NOFOLLOW", 0), dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd, path.name
    finally:
        os.close(fd)


def read_file(path, limit=MAX_BYTES):
    path = no_symlinks(path)
    flags = os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
    try:
        with parent_fd(path) as (parent, name):
            fd = os.open(name, flags, dir_fd=parent)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode), "input_not_regular")
            require(before.st_size <= limit, "input_too_large")
            data = bytearray()
            while len(data) <= limit:
                part = os.read(fd, min(65536, limit + 1 - len(data)))
                if not part:
                    break
                data.extend(part)
            after = os.fstat(fd)
            require(len(data) <= limit, "input_too_large")
            require(before.st_size == after.st_size == len(data) and
                    before.st_mtime_ns == after.st_mtime_ns and
                    before.st_ctime_ns == after.st_ctime_ns, "input_changed")
            return bytes(data)
        finally:
            os.close(fd)
    except OSError:
        raise ProfileError("input_read_failed") from None


def new_file(path, data):
    path = no_symlinks(path)
    try:
        with parent_fd(path) as (parent, name):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as out:
            out.write(data)
    except OSError:
        raise ProfileError("output_exists_or_unwritable") from None


def finite_tree(obj):
    if isinstance(obj, float):
        require(math.isfinite(obj), "nonfinite_parameter")
    elif isinstance(obj, dict):
        for value in obj.values():
            finite_tree(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            finite_tree(value)


def parse_xml(data):
    # Decode before screening: a UTF-16 DOCTYPE must not evade the check.
    try:
        text = data.decode("utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff")
                           else "utf-8-sig")
        require("<!DOCTYPE" not in text.upper() and "<!ENTITY" not in text.upper(),
                "xml_declarations_forbidden")
        root = ET.fromstring(text)
    except (ET.ParseError, UnicodeError):
        raise ProfileError("invalid_xml") from None
    require(root.tag == "device_data", "unsupported_xml_schema", 3)
    todo, count = [(root, 0)], 0
    while todo:
        el, depth = todo.pop()
        count += 1
        require(count <= MAX_NODES and depth <= MAX_DEPTH and len(el) <= 512,
                "xml_complexity_limit")
        require(len(el.attrib) <= 24, "xml_attribute_limit")
        require(all(len(v) <= 8192 for v in el.attrib.values()), "xml_value_limit")
        require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,95}", el.tag), "xml_tag_invalid")
        require(not any(k.lower() in ("href", "src", "path", "file", "filename")
                        for k in el.attrib), "external_reference")
        todo.extend((ch, depth + 1) for ch in el)
    constants = root.findall("constant")
    require(len(constants) == 1, "ambiguous_constants")
    require(len({c.tag for c in constants[0]}) == len(constants[0]), "duplicate_constant")
    for el in root.iter():
        if "preset" in el.attrib:
            ref = el.get("preset")
            require(bool(NAME.fullmatch(ref)), "invalid_constant_reference")
            require(constants[0].find(ref) is not None, "missing_constant_reference")
    # Validate every numeric profile/constant field before upstream's tolerant parser.
    for branch in [constants[0], *root.findall("endpoint")]:
        for el in branch.iter():
            for key, raw in el.attrib.items():
                if key not in ("value", "target", "fs_48000", "f0", "gain", "q", "s",
                               "order", "speaker", "enabled"):
                    continue
                if not raw:
                    require(el.tag == "coefficient", "empty_numeric_parameter")
                    continue
                parts = raw.split(",")
                require(len(parts) <= 256, "numeric_array_limit")
                try:
                    vals = [float(v) for v in parts]
                except ValueError:
                    raise ProfileError("invalid_numeric_parameter") from None
                require(all(math.isfinite(v) and abs(v) <= 1e9 for v in vals),
                        "nonfinite_or_excessive_parameter")
                if key not in ("f0", "gain", "q", "s"):
                    require(all(re.fullmatch(r"[+-]?\d+", v.strip()) for v in parts),
                            "integer_parameter_required")
    endpoints = root.findall("endpoint")
    require(len(list(root.iter("endpoint"))) == len(endpoints), "nested_endpoint")
    require(len(list(root.iter("profile"))) == sum(len(e.findall("profile")) for e in endpoints),
            "nested_profile")
    pairs = [(e.get("type"), e.get("operating_mode")) for e in endpoints]
    require(len(set(pairs)) == len(pairs), "duplicate_endpoint")
    for ep in endpoints:
        require(all(NAME.fullmatch(v or "") for v in
                    (ep.get("type"), ep.get("operating_mode"))), "invalid_endpoint_name")
        names = [p.get("type") for p in ep.findall("profile")]
        require(all(NAME.fullmatch(n or "") for n in names), "invalid_profile_name")
        require(len(set(names)) == len(names), "duplicate_profile")
        for prof in ep.findall("profile"):
            for el in prof.iter():
                if el.tag in ("speaker-peq-filters", "filter_coefficients"):
                    continue  # Repeated filters/coefficient records have schema order.
                tags = [c.tag for c in el]
                require(len(set(tags)) == len(tags), "duplicate_profile_field")
    return root


def inf_association(data, xml_name, codec, subsystem):
    try:
        text = data.decode("utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff")
                           else "utf-8-sig")
    except UnicodeError:
        raise ProfileError("invalid_inf") from None
    sections, current = {}, None
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].lower()
            require(current not in sections, "duplicate_inf_section")
            sections[current] = []
        elif current:
            sections[current].append(line)
    hw = f"VEN_{codec[:4]}&DEV_{codec[4:]}&SUBSYS_{subsystem}".upper()
    installs = set()
    for name, lines in sections.items():
        if not name.startswith("deviceextensions."):
            continue
        for line in lines:
            if "=" not in line:
                continue
            parts = [p.strip() for p in line.split("=", 1)[1].split(",")]
            if any(re.fullmatch(r"(?:HDAUDIO|INTELAUDIO)\\(?:FUNC_[0-9A-F]{2}&)?" + re.escape(hw) +
                               r"(?:&[A-Z0-9_]+)*", p.upper()) for p in parts[1:]):
                installs.add(parts[0].lower())
    require(len(installs) == 1, "inf_hardware_association_missing_or_ambiguous")
    install = next(iter(installs))
    copy_sections = []
    for name, lines in sections.items():
        if name == install + ".nt":
            for line in lines:
                if "=" in line and line.split("=", 1)[0].strip().lower() == "copyfiles":
                    copy_sections.extend(p.strip().lower() for p in line.split("=", 1)[1].split(","))
    copied = [l for s in copy_sections for l in sections.get(s, [])
              if l.split(",")[0].strip().strip('"').lower() == xml_name.lower()]
    require(copied,
            "inf_selected_install_does_not_copy_xml")
    for line in copied:
        fields = [p.strip().strip('"').lower() for p in line.split(",")]
        require(len(fields) == 1 or fields[1] in ("", xml_name.lower()),
                "inf_renamed_xml_copy_unsupported", 3)
    require(any(l.split("=", 1)[0].strip().strip('"').lower() == xml_name.lower()
                for n, lines in sections.items() if n.startswith("sourcedisksfiles")
                for l in lines), "inf_xml_not_in_source_files")


def inputs(args):
    xml, inf = read_file(args.xml), read_file(args.inf)
    inventory_bytes = read_file(args.inventory)
    inventory = json_load(inventory_bytes)
    hardware = inventory["hardware"]
    source_hash = None
    if isinstance(hardware.get("codec"), dict):
        codec, subsystem = hardware["codec"]["vendor_id"], hardware["codec"]["subsystem_id"]
    else:
        codec, subsystem = hardware["codec_vendor_id"], hardware["subsystem_id"]
    codec, subsystem = codec.lower().removeprefix("0x"), subsystem.lower().removeprefix("0x")
    require(ID.fullmatch(codec) and ID.fullmatch(subsystem), "invalid_hardware_id")
    require((codec, subsystem) in DEVICE_CONTRACTS, "unsupported_hardware", 3)
    contract = DEVICE_CONTRACTS[codec, subsystem]
    if subsystem == "10431c63":
        require(hardware["amplifiers"]["model"] == "Cirrus CS35L56" and
                hardware["amplifiers"]["count"] == 2 and
                hardware["amplifiers"]["speaker_id"] == 0, "unsupported_amplifier_identity", 3)
        oem = inventory["oem"]
    else:
        require(hardware["manufacturer"].lower() == "lenovo" and
                hardware["product_model"].startswith("20MF") and hardware["generation"] == 1,
                "model_identity_mismatch")
        require(any(p["vendor"].lower() == "0x8086" and p["device"].lower() == "0xa348" and
                    p["subsystem_vendor"].lower() == "0x17aa" and
                    p["subsystem_device"].lower() == "0x2267" for p in hardware["audio_pci"]),
                "pci_identity_mismatch")
        source_bytes = read_file(ROOT / contract["source_manifest"])
        source_hash = digest(source_bytes)
        oem = json_load(source_bytes)["oem"]
    require(Path(args.xml).name == oem["xml_name"], "xml_filename_mismatch")
    require(Path(args.inf).name == oem["inf_name"], "inf_filename_mismatch")
    require(digest(xml) == oem["xml_sha256"] and len(xml) == oem["xml_size_bytes"] and
            digest(inf) == oem["inf_sha256"] and len(inf) == oem["inf_size_bytes"],
            "inventory_hash_or_size_mismatch")
    require(oem["xml_name"].lower() == contract["xml_name"].lower(), "xml_hardware_filename_mismatch")
    root = parse_xml(xml)
    inf_association(inf, oem["xml_name"], codec, subsystem)
    duplicate = "not-verified"
    if args.duplicate_xml:
        other = read_file(args.duplicate_xml)
        require(other == xml, "duplicate_xml_disagrees")
        duplicate = "byte-identical"
    hashes = {"xml_sha256": digest(xml), "inf_sha256": digest(inf),
              "inventory_sha256": digest(inventory_bytes), "duplicate_xml": duplicate}
    if source_hash:
        hashes["source_manifest_sha256"] = source_hash
    return root, xml, hashes, dict(contract["bundle_hardware"])


@contextlib.contextmanager
def converter(path):
    """Snapshot only pinned runtime bytes; no .pyc or untracked import is used."""
    source = json_load(read_file(SOURCE_MANIFEST))["converter"]
    require(source["commit"] == PIN, "converter_pin_mismatch", 3)
    path = no_symlinks(path)
    require(not any(n == "lib" or n.startswith("lib.") for n in sys.modules),
            "converter_module_collision", 3)
    with tempfile.TemporaryDirectory(prefix="speaker-source-") as tmp:
        tmp = Path(tmp)
        for name, expected in source["runtime_files"].items():
            require(name.startswith("lib/") and ".." not in Path(name).parts and
                    name.endswith(".py"), "invalid_source_manifest", 3)
            data = read_file(path / name)
            require(digest(data) == expected, "converter_source_hash_mismatch", 3)
            dest = tmp / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        sys.path.insert(0, str(tmp))
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                yield importlib.import_module("lib.dax.parse"), importlib.import_module("lib.preset.fir"), \
                    importlib.import_module("lib.preset.bands"), importlib.import_module("lib.preset.plugins")
        finally:
            sys.path.remove(str(tmp))
            for name in list(sys.modules):
                if name == "lib" or name.startswith("lib."):
                    del sys.modules[name]


def select(root, args):
    identity = (args.codec.lower(), args.subsystem.lower())
    require(identity in DEVICE_CONTRACTS, "hardware_mismatch")
    require(args.endpoint == "internal_speaker" and args.mode == "normal",
            "unsupported_endpoint_or_mode", 3)
    require(NAME.fullmatch(args.profile), "invalid_profile_name")
    eps = [e for e in root.findall("endpoint") if e.get("type") == args.endpoint and
           e.get("operating_mode") == args.mode]
    require(len(eps) == 1, "endpoint_match_not_unique")
    ep = eps[0]
    counts = {"total_count": "2", "front_count": "2", "side_count": "0",
              "height_count": "0", "has_subwoofer": "0"}
    if DEVICE_CONTRACTS[identity]["layout"] == "front-stereo":
        layout_ok = all(ep.get(k) == v for k, v in counts.items())
    else:
        layout_ok = ep.get("ch_count") == "2" and all(ep.get(k, v) == v for k, v in counts.items())
    require(ep.get("fs") == "48000" and layout_ok, "unsupported_rate_or_channel_layout", 3)
    profiles = [p for p in ep.findall("profile") if p.get("type") == args.profile]
    require(len(profiles) == 1, "profile_match_not_unique")
    return profiles[0]


def validate_tuning(t):
    finite_tree(vars(t))
    require(len(t.freqs) == 20 and all(0 < f < 24000 for f in t.freqs) and
            sorted(set(t.freqs)) == t.freqs, "unsupported_frequency_grid", 3)
    require(len(t.ao_left) == len(t.ao_right) == 20 and
            all(len(v) == 20 for v in t.curves.values()), "curve_length_mismatch")
    require(0 <= t.ieq_amount <= 100, "ieq_amount_out_of_range")
    require(all(abs(v) <= 960 for seq in [t.ao_left, t.ao_right, *t.curves.values()]
                for v in seq), "curve_gain_out_of_range")
    require(len(t.peq_filters) <= 32, "peq_count_limit")
    if t.vol_leveler:
        require(t.vol_leveler["enable"] in (0, 1) and 0 <= t.vol_leveler["amount"] <= 10 and
                -80 <= t.vol_leveler["in_target"] <= 0 and -80 <= t.vol_leveler["out_target"] <= 0,
                "leveler_parameter_out_of_range")
    if t.dialog_enhancer:
        require(0 <= t.dialog_enhancer["amount"] <= 16, "dialog_parameter_out_of_range")
    for f in t.peq_filters:
        require(f["speaker"] in (0, 1) and f["type"] in (1, 3, 4, 6, 7, 8, 9),
                "unsupported_peq_filter", 3)
        require(0 < f["f0"] < 24000 and abs(f["gain"]) <= 60 and
                0.1 <= f["q"] <= 30 and 0 < f["s"] <= 1, "peq_parameter_out_of_range")
        if f["type"] in (6, 7, 8, 9):
            require(f["order"] in (2, 4, 6, 8), "unsupported_peq_order", 3)
    # Upstream's dynamics decoding is explicitly an approximation and defaults
    # some invalid coefficients. Refuse those defaults rather than hide bad data.
    if t.mb_comp:
        m = t.mb_comp
        require(1 <= m["group_count"] <= 4 and len(m["band_groups"]) >= m["group_count"],
                "invalid_compressor_groups")
        for i, band in enumerate(m["band_groups"][:m["group_count"]]):
            # The first item is a band-grid INDEX; the last band's 20 is a
            # Nyquist sentinel. Threshold/makeup use Q4 dB, not Q15 gains.
            require(0 <= band[0] <= (20 if i == m["group_count"] - 1 else 19) and
                    0 < band[2] <= 32768 and 0 < band[3] < 32768 and
                    0 < band[4] < 32768 and abs(band[1]) <= 1920 and abs(band[5]) <= 960,
                    "invalid_compressor_coefficient")


def validate_selected_profile(profile):
    # Unlike the tolerant upstream parser, this tool must not silently drop an
    # enabled filter or invent defaults for a malformed selected filter.
    direct = profile.findall("tuning-vlldp/speaker-peq-filters")
    require(len(list(profile.iter("speaker-peq-filters"))) == len(direct), "nested_peq_filters")
    for el in profile.findall("tuning-vlldp/speaker-peq-filters/filter"):
        require(set(el.attrib) <= {"enabled", "type", "speaker", "f0", "gain", "q", "s", "order"},
                "unknown_peq_attribute", 3)
        require(all(k in el.attrib for k in ("enabled", "type", "speaker", "f0")),
                "missing_peq_attribute")
        require(el.get("enabled") in ("0", "1"), "invalid_peq_enable")
        if el.get("enabled") == "1":
            require(el.get("type") in ("1", "3", "4", "6", "7", "8", "9"),
                    "unsupported_peq_filter", 3)
            require(el.get("speaker") in ("0", "1"), "unsupported_peq_channel", 3)


def make_speaker_peq(bands, filters):
    """Retain supplied upstream bands; pad asymmetric channels with unity EQ.

    Upstream pads HP/LP categories with active pass filters. A channel without
    that source filter must instead get a zero-gain bell, which is neutral.
    The category order/counts come from the hash-pinned builder itself.
    """
    eq = bands.make_peq_eq(filters)
    if eq is None:
        return None
    offset = 0
    for category in bands._PEQ_CATEGORIES:
        counts = [sum(f["speaker"] == channel and f["type"] in category.types
                      for f in filters) for channel in (0, 1)]
        width = max(counts)
        for channel, count in zip(("left", "right"), counts):
            for index in range(count, width):
                eq[channel][f"band{offset + index}"] = bands.make_band(1000.0, 0.0)
        offset += width
    return eq


def field_report(profile, root, stages, voicing="balanced"):
    """Every selected profile leaf is reported, including unsupported ones."""
    rows = []
    emitted = {s["name"]: s for s in stages}
    enable_paths = {"equalizer#0": "tuning-vlldp/speaker-peq-enable",
                    "equalizer#1": "tuning-cp/dialog-enhancer-enable",
                    "autogain#0": "tuning-cp/volume-leveler-enable",
                    "multiband_compressor#0": "tuning-vlldp/mb-compressor-enable",
                    "multiband_compressor#1": "tuning-vlldp/regulator-speaker-dist-enable"}
    static = {
        "tuning-vlldp/audio-optimizer-enable": ("convolver#0", "0/1 enable"),
        "tuning-vlldp/audio-optimizer-bands/ch_00": ("convolver#0", "raw/16 dB; FL"),
        "tuning-vlldp/audio-optimizer-bands/ch_01": ("convolver#0", "raw/16 dB; FR"),
        "tuning-vlldp/audio-optimizer-bands/gain_l": ("convolver#0", "raw/16 dB; FL"),
        "tuning-vlldp/audio-optimizer-bands/gain_r": ("convolver#0", "raw/16 dB; FR"),
        "tuning-vlldp/speaker-peq-enable": ("equalizer#0", "0/1 enable"),
        "tuning-vlldp/speaker-peq-filters/filter": ("equalizer#0", "Hz/dB/Q/slope/order"),
        "tuning-cp/ieq-enable": ("convolver#0", "0/1 enable"),
        "tuning-cp/ieq-amount": ("convolver#0", "raw/100 static weight")}
    approximated = {
        "tuning-cp/volume-leveler-enable", "tuning-cp/volume-leveler-amount",
        "tuning-cp/volume-leveler-out-target",
        "tuning-cp/dialog-enhancer-enable", "tuning-cp/dialog-enhancer-amount",
        "tuning-vlldp/mb-compressor-enable",
        "tuning-vlldp/mb-compressor-tuning/group_count",
        *("tuning-vlldp/mb-compressor-tuning/band_group_" + str(i) for i in range(4)),
        "tuning-vlldp/regulator-speaker-dist-enable",
        "tuning-vlldp/regulator-tuning/threshold_high",
        "tuning-vlldp/regulator-tuning/isolated_band"}

    def walk(el, path):
        if len(el):
            for i, child in enumerate(el):
                # Index all siblings so repeated filters stay distinguishable.
                walk(child, path + "/" + child.tag + f"[{i}]")
            return
        clean = re.sub(r"\[\d+\]", "", path)
        if clean in static:
            stage, unit = static[clean]
            status = "mapped-static-approximation"
            approx = "Enable-gated static response; IEQ steering omitted; FIR at 48 kHz."
        elif clean in approximated or re.fullmatch(
                r"tuning-vlldp/regulator-tuning/(?:threshold_high|isolated_band)/ch_00", clean):
            if "volume-leveler" in clean:
                stage, unit = "autogain#0", "enable 0/1; amount 0..10; out-target raw/16 dBFS"
            elif "dialog-enhancer" in clean:
                stage, unit = "equalizer#1", "amount/16 * 6 dB at 2500 Hz, Q=0.7; enable 0/1"
            elif "mb-compressor" in clean:
                stage, unit = "multiband_compressor#0", "group: grid index, Q4 threshold, Q15 inverse ratio, Q15 block-256 attack/release, Q4 makeup"
            else:
                stage, unit = "multiband_compressor#1", "threshold raw/16 dBFS; isolation 0/1; ch_00 stereo reference"
            status = "approximation-bypassed" if emitted.get(stage, {}).get("bypassed") else "approximation-emitted"
            approx = "Approximate EasyEffects stage is emitted " + \
                ("bypassed" if status == "approximation-bypassed" else "active") + \
                "; thresholds/time constants/ratios are unqualified."
        else:
            stage, status = None, "unsupported"
            unit, approx = "not interpreted", "No equivalent processing stage is emitted."
        if stage is not None and stage not in emitted:
            enable = profile.find(enable_paths[stage]) if stage in enable_paths else None
            disabled = enable is not None and enable.get("value") == "0"
            status = "disabled" if disabled else "not-emitted"
            approx = "Source stage is disabled; no preset stage emitted." if disabled else \
                "No preset stage emitted for these fields."
            stage = None
        rows.append({"source": path, "raw_attributes": dict(el.attrib), "unit_scale": unit,
                     "output_stage": stage, "status": status, "approximation": approx})

    for el in profile:
        walk(el, el.tag)
    for el in root.find("constant"):
        if el.tag == "band_20_freq" or el.tag.startswith("ieq_"):
            used = el.tag in ("band_20_freq", "ieq_" + voicing)
            rows.append({"source": "constant/" + el.tag, "raw_attributes": dict(el.attrib),
                         "unit_scale": "Hz for grid; raw/16 dB for IEQ",
                         "output_stage": "convolver#0" if used and "convolver#0" in emitted else None,
                         "status": ("mapped-static-approximation" if "convolver#0" in emitted else "not-emitted")
                         if used else "not-selected",
                         "approximation": "Selected voicing only; log-frequency interpolation."})
    return {"schema_version": 1, "complete_equivalence": False, "fields": rows,
            "stages": stages, "limits": [
                "No host Atmos decoding/rendering, volume-dependent model or media-intelligence steering.",
                "OEM loudness gain, virtual bass and gain restoration suppressed.",
                "Dynamics approximations bypassed pending reference and physical qualification.",
                "Final limiter is a sample-peak stage, not amplifier thermal/excursion protection.",
                "No amplifier firmware/calibration or controls are modified; protection is not qualified."]}


def build(args):
    root, xml, hashes, hardware = inputs(args)
    require(args.codec.lower() == hardware["codec"] and args.subsystem.lower() == hardware["subsystem"],
            "hardware_mismatch")
    prof = select(root, args)
    validate_selected_profile(prof)
    # Never create the requested destination until parsing and DSP succeed.
    output = no_symlinks(args.output)
    require(not output.exists(), "output_exists_or_unwritable")
    require(output.parent.is_dir(), "output_parent_missing")
    with converter(args.converter) as (parse, fir, bands, plugins):
        import numpy as np
        import scipy
        from scipy.io import wavfile
        from scipy.signal import chirp, fftconvolve
        with tempfile.TemporaryDirectory(prefix="speaker-input-") as temp:
            snapshot = Path(temp) / "input.xml"
            snapshot.write_bytes(xml)
            tuning = parse.parse_xml(snapshot, args.endpoint, args.mode, args.profile)
        validate_tuning(tuning)
        curve = "ieq_" + args.voicing
        require(curve in tuning.curves, "voicing_unavailable", 3)
        weight = tuning.ieq_amount / 100 if tuning.ieq_enabled else 0
        target = [np.asarray(ao, dtype=float) / 16 +
                  np.asarray(tuning.curves[curve], dtype=float) / 16 * weight
                  for ao in (tuning.ao_left, tuning.ao_right)]
        designed = [fir.make_fir(tuning.freqs, gains, normalize=False) for gains in target]
        common_peak_db = max(v[1] for v in designed)
        # A common attenuation only; even all-cut profiles are never boosted.
        attenuation = max(0.0, common_peak_db)
        taps = np.column_stack([v[0] for v in designed]) * 10 ** (-attenuation / 20)
        require(np.isfinite(taps).all() and taps.shape == (4096, 2), "invalid_fir_output")
        taps = taps.astype(np.float32)
        stem = "speaker-" + digest(taps.tobytes())[:16]
        convolver = bands.make_convolver(stem)
        eq = make_speaker_peq(bands, tuning.peq_filters)
        if eq:
            # Sum all positive peaks for each channel, rather than upstream's
            # maximum single bandwidth-weighted boost. This remains an estimate.
            boost = max(sum(max(0.0, f["gain"]) for f in tuning.peq_filters
                            if f["speaker"] == c and f["type"] in (1, 3, 4)) for c in (0, 1))
            eq["output-gain"] = -round(boost, 6)
        stages = [("convolver#0", convolver), ("equalizer#0", eq)]
        for name, value in [
            ("equalizer#1", plugins.make_dialog_enhancer(tuning.dialog_enhancer)),
            ("autogain#0", plugins.make_autogain(tuning.vol_leveler)),
            ("multiband_compressor#0", plugins.make_multiband_compressor(tuning.mb_comp, tuning.freqs)),
            ("multiband_compressor#1", plugins.make_regulator(tuning.regulator, tuning.freqs, volmax_boost=0))]:
            if value:
                value["bypass"] = True
            stages.append((name, value))
        stages.append(("limiter#0", plugins.make_limiter(input_gain=0)))
        out = {"blocklist": [], "plugins_order": [n for n, v in stages if v]}
        out.update({n: v for n, v in stages if v})
        preset = {"_generator": "rog_audio offline-speaker schema-1", "output": out}
        finite_tree(preset)
        stage_summary = [{"name": n, "bypassed": bool(v["bypass"])} for n, v in stages if v]
        report = field_report(prof, root, stage_summary, args.voicing)
        report["interpreted_selection"] = {"ieq_enabled": tuning.ieq_enabled,
            "ieq_weight": weight, "ieq_weight_source": "explicit" if prof.find("tuning-cp/ieq-amount") is not None else "upstream-default-10-percent",
            "optimizer_enabled": tuning.ao_enabled,
            "dynamics_emitted": [n for n, v in stages if v and v["bypass"]]}
        # A synthetic full-scale impulse/sweep tests the FIR only. Neither this
        # nor the frequency peak is a bound on the complete runtime DSP chain.
        impulse_peak = float(np.max(np.abs(taps)))
        time = np.arange(48000, dtype=float) / 48000
        sweep = chirp(time, f0=20, f1=20000, t1=1, method="logarithmic")
        rendered = np.column_stack([fftconvolve(sweep, taps[:, c]) for c in (0, 1)])
        require(np.isfinite(rendered).all(), "nonfinite_sweep")
        spectrum = np.fft.rfft(taps, axis=0)
        actual = 20 * np.log10(np.abs(spectrum) + 1e-12)
        bins = np.fft.rfftfreq(4096, d=1/48000)
        expected = np.column_stack([fir.interpolate_curve_db(np.asarray(tuning.freqs), g, bins)
                                    - attenuation for g in target])
        error = float(np.max(np.abs(actual - expected)))
        require(error < 0.01, "fir_response_mismatch")
        report["signal_checks"] = {"scope": "FIR-only synthetic; no EasyEffects runtime",
            "sample_rate_hz": 48000, "channels": ["FL", "FR"], "frames": 4096,
            "fir_attenuation_db": attenuation, "fir_peak_frequency_gain_db": float(actual.max()),
            "fir_shape_max_error_db": error, "impulse_sample_peak": impulse_peak,
            "sweep_sample_peak": float(np.max(np.abs(rendered))),
            "sweep_samples_over_full_scale": int((np.abs(rendered) > 1).sum()),
            "fir_l1_norm_bound": [float(np.sum(np.abs(taps[:, c]))) for c in (0, 1)],
            "headroom_scope": "FIR frequency normalisation plus PEQ positive-gain estimate; not a physical safety bound"}
        buf = io.BytesIO()
        wavfile.write(buf, 48000, taps)
        files = {"preset.json": json_bytes(preset), "field-mapping.json": json_bytes(report),
                 "irs/" + stem + ".irs": buf.getvalue()}
        manifest = {"schema_version": 1, "activation_state": "not-installed",
            "qualification": "offline-candidate-unqualified", "converter_commit": PIN,
            "dependencies": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
            "inputs": hashes, "hardware": hardware,
            "selection": {"endpoint": args.endpoint, "mode": args.mode, "profile": args.profile, "voicing": args.voicing},
            "sample_rate_hz": 48000, "channels": ["FL", "FR"],
            "outputs": {n: digest(b) for n, b in files.items()}, "preset": "preset.json",
            "mapping_report": "field-mapping.json", "impulse": "irs/" + stem + ".irs"}
        files["manifest.json"] = json_bytes(manifest)
    # Exclusive directory ownership: no deletion or overwrite of existing output.
    try:
        with parent_fd(output) as (parent, name):
            os.mkdir(name, mode=0o700, dir_fd=parent)
    except OSError:
        raise ProfileError("output_exists_or_unwritable") from None
    try:
        with parent_fd(output / "irs") as (parent, name):
            os.mkdir(name, mode=0o700, dir_fd=parent)
        for name, data in files.items():
            new_file(output / name, data)
        verify(output)
    except Exception:
        # Only our newly-created directory is removed after an incomplete write.
        with parent_fd(output) as (parent, name):
            shutil.rmtree(name, dir_fd=parent)
        raise
    return {"result": "built", "activation_state": "not-installed",
            "qualification": "offline-candidate-unqualified",
            "manifest_sha256": digest(files["manifest.json"])}


def bundle_name(value):
    require(isinstance(value, str) and bool(re.fullmatch(
        r"(?:preset\.json|field-mapping\.json|irs/speaker-[0-9a-f]{16}\.irs)", value)),
        "invalid_bundle_reference")
    return value


def verify(bundle):
    bundle = no_symlinks(bundle)
    require(bundle.is_dir(), "bundle_not_directory")
    manifest = json_load(read_file(bundle / "manifest.json"))
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
            "unsupported_bundle_schema")
    require(manifest["activation_state"] == "not-installed" and
            manifest["qualification"] == "offline-candidate-unqualified" and
            manifest["converter_commit"] == PIN and manifest["sample_rate_hz"] == 48000 and
            manifest["channels"] == ["FL", "FR"], "invalid_bundle_contract")
    hardware = manifest["hardware"]
    identity = (hardware["codec"], hardware["subsystem"])
    require(identity in DEVICE_CONTRACTS and hardware == DEVICE_CONTRACTS[identity]["bundle_hardware"],
            "invalid_bundle_hardware")
    sel = manifest["selection"]
    require(sel["endpoint"] == "internal_speaker" and sel["mode"] == "normal" and
            NAME.fullmatch(sel["profile"]) and sel["voicing"] in ("balanced", "detailed", "warm"),
            "invalid_bundle_selection")
    for k in ("xml_sha256", "inf_sha256", "inventory_sha256"):
        require(DIGEST.fullmatch(manifest["inputs"][k]), "invalid_input_hash")
    if identity[1] == "17aa2276":
        require(DIGEST.fullmatch(manifest["inputs"]["source_manifest_sha256"]), "invalid_source_hash")
    require(manifest["inputs"]["duplicate_xml"] in ("not-verified", "byte-identical"),
            "invalid_duplicate_state")
    outputs = manifest["outputs"]
    require(isinstance(outputs, dict) and len(outputs) == 3, "invalid_output_inventory")
    expected = {"manifest.json"}
    for name, sha in outputs.items():
        bundle_name(name)
        require(isinstance(sha, str) and DIGEST.fullmatch(sha), "invalid_output_hash")
        require(digest(read_file(bundle / name)) == sha, "output_hash_mismatch")
        expected.add(name)
    actual = set()
    for parent, dirs, files in os.walk(bundle, followlinks=False):
        for name in dirs + files:
            p = Path(parent) / name
            require(not p.is_symlink(), "symlink_path")
        for name in files:
            actual.add(str((Path(parent) / name).relative_to(bundle)))
    require(actual == expected, "unexpected_or_missing_bundle_file")
    require(manifest["preset"] == "preset.json" and manifest["mapping_report"] == "field-mapping.json",
            "invalid_bundle_reference")
    impulse = bundle_name(manifest["impulse"])
    require(impulse.startswith("irs/") and impulse in outputs, "invalid_impulse_reference")
    preset = json_load(read_file(bundle / "preset.json"))
    report = json_load(read_file(bundle / "field-mapping.json"))
    require(report["schema_version"] == 1 and report["complete_equivalence"] is False and
            isinstance(report["fields"], list) and report["fields"], "invalid_mapping_report")
    out = preset["output"]
    order = out["plugins_order"]
    require(isinstance(order, list) and len(order) == len(set(order)) and
            set(out) == set(order) | {"plugins_order", "blocklist"} and out["blocklist"] == [],
            "invalid_preset_stages")
    require(order[0] == "convolver#0" and order[-1] == "limiter#0" and
            set(order) <= {"convolver#0", "equalizer#0", "equalizer#1", "autogain#0",
                           "multiband_compressor#0", "multiband_compressor#1", "limiter#0"},
            "unsupported_preset_stage")
    require(out["convolver#0"]["kernel-name"] == Path(impulse).stem and
            out["convolver#0"]["autogain"] is False, "invalid_kernel_reference")
    for name in order:
        stage = out[name]
        require(type(stage["bypass"]) is bool and stage["input-gain"] == 0 and
                stage["output-gain"] <= 0, "invalid_stage_gain")
        require(stage["bypass"] == (name in ("equalizer#1", "autogain#0", "multiband_compressor#0",
                                             "multiband_compressor#1")), "invalid_bypass_state")
    require(report["stages"] == [{"name": n, "bypassed": out[n]["bypass"]} for n in order],
            "mapping_stage_inventory_mismatch")
    for field in report["fields"]:
        stage = field["output_stage"]
        require(stage is None or stage in order, "mapping_reference_not_emitted")
        if field["status"] == "approximation-bypassed":
            require(stage in order and out[stage]["bypass"], "mapping_bypass_mismatch")
        elif field["status"] in ("disabled", "not-emitted"):
            require(stage is None, "mapping_absent_stage_reference")
    finite_tree(preset)
    finite_tree(report)
    # A minimal RIFF parser verifies format without requiring numpy/scipy.
    wav = read_file(bundle / impulse)
    require(wav[:4] == b"RIFF" and wav[8:12] == b"WAVE" and
            struct.unpack_from("<I", wav, 4)[0] + 8 == len(wav), "invalid_impulse_wav")
    offset, chunks = 12, {}
    while offset + 8 <= len(wav):
        tag, size = wav[offset:offset+4], struct.unpack_from("<I", wav, offset+4)[0]
        require(tag not in chunks and offset + 8 + size <= len(wav), "invalid_wav_chunk")
        chunks[tag] = wav[offset+8:offset+8+size]
        offset += 8 + size + size % 2
    require(offset == len(wav), "invalid_wav_length")
    fmt = chunks.get(b"fmt ", b"")
    require(len(fmt) >= 16 and struct.unpack_from("<HHIIHH", fmt) ==
            (3, 2, 48000, 384000, 8, 32), "unsupported_impulse_format")
    samples = chunks.get(b"data", b"")
    require(len(samples) == 4096 * 8, "invalid_impulse_frame_count")
    require(all(math.isfinite(v[0]) for v in struct.iter_unpack("<f", samples)),
            "nonfinite_impulse")
    require(Path(impulse).stem == "speaker-" + digest(samples)[:16], "impulse_name_mismatch")
    return {"result": "verified", "activation_state": "not-installed",
            "qualification": "offline-candidate-unqualified"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Write private metadata; no conversion or activation")
    make = sub.add_parser("build", help="Write a new private, unqualified offline bundle")
    for p in (inspect, make):
        p.add_argument("--xml", required=True, type=Path)
        p.add_argument("--inf", required=True, type=Path)
        p.add_argument("--inventory", type=Path, default=INVENTORY)
        p.add_argument("--duplicate-xml", type=Path)
    inspect.add_argument("--report", required=True, type=Path)
    for key in ("codec", "subsystem", "endpoint", "mode", "profile"):
        make.add_argument("--" + key, required=True)
    make.add_argument("--voicing", choices=("balanced", "detailed", "warm"), default="balanced")
    make.add_argument("--converter", required=True, type=Path)
    make.add_argument("--output", required=True, type=Path)
    check = sub.add_parser("verify", help="Verify offline bundle integrity and contract")
    check.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            root, _, hashes, hardware = inputs(args)
            new_file(args.report, json_bytes({"schema_version": 1, "inputs": hashes,
                "hardware": hardware, "endpoints": [{"endpoint": e.get("type"),
                    "mode": e.get("operating_mode"), "profiles": [p.get("type") for p in e.findall("profile")]}
                    for e in root.findall("endpoint")]}))
            result = {"result": "inspected", "activation_state": "not-installed"}
        elif args.command == "build":
            result = build(args)
        else:
            result = verify(args.bundle)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ProfileError as exc:
        print(json.dumps({"result": "failed", "reason": exc.reason}), file=sys.stderr)
        return exc.code
    except ImportError:
        print('{"result":"failed","reason":"missing_dependency"}', file=sys.stderr)
        return 3
    except (KeyError, TypeError, ValueError, OSError, AttributeError, IndexError,
            OverflowError, RecursionError, struct.error):
        print('{"result":"failed","reason":"invalid_schema_or_operation"}', file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
