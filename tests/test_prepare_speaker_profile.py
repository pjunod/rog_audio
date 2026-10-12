"""Synthetic DAX3 inputs only: never discover or copy private OEM files."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

SPEC = importlib.util.spec_from_file_location(
    "prepare_speaker_profile", Path(__file__).resolve().parents[1] / "scripts/prepare_speaker_profile.py")
speaker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(speaker)

XML_NAME = "DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml"
INF_NAME = "dax3_ext_rtk.inf"
FREQS = [20, 30, 45, 65, 95, 140, 200, 300, 440, 640,
         930, 1350, 1950, 2800, 4050, 5850, 8450, 12200, 17600, 20000]


def fixture():
    """Construct public-schema fields with deliberately invented values."""
    r = ET.Element("device_data")
    const = ET.SubElement(r, "constant")
    ET.SubElement(const, "band_20_freq", fs_48000=",".join(map(str, FREQS)))
    for name, value in (("balanced", 16), ("detailed", 32), ("warm", -16)):
        ET.SubElement(const, "ieq_" + name, target=",".join([str(value)] * 20))
    ep = ET.SubElement(r, "endpoint", type="internal_speaker", operating_mode="normal",
                       fs="48000", total_count="2", front_count="2", side_count="0",
                       height_count="0", has_subwoofer="0")
    for name in ("music", "dynamic", "off"):
        p = ET.SubElement(ep, "profile", type=name)
        cp = ET.SubElement(p, "tuning-cp")
        ET.SubElement(cp, "ieq-enable", value="0" if name == "off" else "1")
        ET.SubElement(cp, "ieq-amount", value="10")
        ET.SubElement(cp, "unknown-future-stage", value="1")
        ET.SubElement(cp, "volmax-boost", value="96")
        vl = ET.SubElement(p, "tuning-vlldp")
        ET.SubElement(vl, "audio-optimizer-enable", value="0" if name == "off" else "1")
        ao = ET.SubElement(vl, "audio-optimizer-bands")
        ET.SubElement(ao, "ch_00", value=",".join(["16"] * 20))
        ET.SubElement(ao, "ch_01", value=",".join(["-16"] * 20))
        ET.SubElement(vl, "speaker-peq-enable", value="0")
    return r


class PreparationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="speaker-test-")
        self.addCleanup(self.temp.cleanup)
        # macOS /var is a symlink; use its resolved spelling for this fixture.
        self.path = Path(self.temp.name).resolve()
        self.xml = self.path / XML_NAME
        self.inf = self.path / INF_NAME
        self.inventory = self.path / "inventory.json"
        self.root = fixture()
        self.inf.write_text("""[DeviceExtensions.NTamd64]
%Device%=SpeakerInstall,HDAUDIO\\VEN_10EC&DEV_0285&SUBSYS_10431C63
[SpeakerInstall.NT]
CopyFiles=SpeakerTuning
[SpeakerTuning]
DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml
[SourceDisksFiles]
DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml=1
""")
        self.write_fixture()

    def write_fixture(self, data=None):
        self.xml.write_bytes(ET.tostring(self.root) if data is None else data)
        inv = {"hardware": {"codec_vendor_id": "10ec0285", "subsystem_id": "10431c63",
                    "amplifiers": {"model": "Cirrus CS35L56", "count": 2, "speaker_id": 0}},
               "oem": {"xml_name": XML_NAME, "inf_name": INF_NAME,
                       "xml_sha256": speaker.digest(self.xml.read_bytes()),
                       "xml_size_bytes": self.xml.stat().st_size,
                       "inf_sha256": speaker.digest(self.inf.read_bytes()),
                       "inf_size_bytes": self.inf.stat().st_size}}
        self.inventory.write_bytes(speaker.json_bytes(inv))

    def arguments(self, command="inspect", **changes):
        values = dict(xml=self.xml, inf=self.inf, inventory=self.inventory, duplicate_xml=None,
                      codec="10ec0285", subsystem="10431c63", endpoint="internal_speaker",
                      mode="normal", profile="music", voicing="balanced",
                      converter=Path(os.environ.get("ROG_SPEAKER_CONVERTER", "/missing")),
                      output=self.path / "bundle", report=self.path / "report.json", command=command)
        values.update(changes)
        return type("Args", (), values)()

    def fail_inputs(self, reason):
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.inputs(self.arguments())
        self.assertEqual(cm.exception.reason, reason)

    def test_exact_hardware_and_inf_match(self):
        r, _, hashes, hardware = speaker.inputs(self.arguments())
        self.assertEqual(r.tag, "device_data")
        self.assertEqual(hardware["speaker_id"], 0)
        self.assertEqual(hashes["duplicate_xml"], "not-verified")

    def test_inf_wrong_hardware(self):
        self.inf.write_text(self.inf.read_text().replace("10431C63", "10431C64", 1))
        self.write_fixture()
        self.fail_inputs("inf_hardware_association_missing_or_ambiguous")

    def test_inf_function_prefix(self):
        self.inf.write_text(self.inf.read_text().replace("HDAUDIO\\VEN_", "HDAUDIO\\FUNC_01&VEN_"))
        self.write_fixture()
        speaker.inputs(self.arguments())

    def test_inf_comments_not_identity(self):
        self.inf.write_text(self.inf.read_text().replace("%Device%=", ";%Device%="))
        self.write_fixture()
        self.fail_inputs("inf_hardware_association_missing_or_ambiguous")

    def test_inf_wrong_copy_section(self):
        self.inf.write_text(self.inf.read_text().replace("CopyFiles=SpeakerTuning", "CopyFiles=Other"))
        self.write_fixture()
        self.fail_inputs("inf_selected_install_does_not_copy_xml")

    def test_inf_renamed_copy_is_not_input_association(self):
        self.inf.write_text(self.inf.read_text().replace(XML_NAME + "\n", XML_NAME + ",other.xml\n"))
        self.write_fixture()
        self.fail_inputs("inf_renamed_xml_copy_unsupported")

    def test_input_hash_pin(self):
        self.xml.write_bytes(self.xml.read_bytes() + b" ")
        self.fail_inputs("inventory_hash_or_size_mismatch")

    def test_wrong_codec_or_subsystem(self):
        for key, value in (("codec", "10ec0294"), ("subsystem", "10431c64")):
            with self.subTest(key=key), self.assertRaises(speaker.ProfileError) as cm:
                speaker.select(self.root, self.arguments(**{key: value}))
            self.assertEqual(cm.exception.reason, "hardware_mismatch")

    def test_wrong_endpoint_or_mode(self):
        for key, value in (("endpoint", "headphone"), ("mode", "gaming")):
            with self.subTest(key=key), self.assertRaises(speaker.ProfileError) as cm:
                speaker.select(self.root, self.arguments(**{key: value}))
            self.assertEqual(cm.exception.code, 3)

    def test_duplicate_profile(self):
        ET.SubElement(self.root.find("endpoint"), "profile", type="music")
        self.write_fixture()
        self.fail_inputs("duplicate_profile")

    def test_duplicate_endpoint(self):
        self.root.append(ET.fromstring(ET.tostring(self.root.find("endpoint"))))
        self.write_fixture()
        self.fail_inputs("duplicate_endpoint")

    def test_nested_endpoint_does_not_override_validated_selection(self):
        wrapper = ET.Element("hidden")
        wrapper.append(ET.fromstring(ET.tostring(self.root.find("endpoint"))))
        self.root.insert(1, wrapper)
        self.write_fixture()
        self.fail_inputs("nested_endpoint")

    def test_nested_profile_rejected(self):
        ET.SubElement(self.root, "hidden").append(ET.fromstring(ET.tostring(self.root.find("endpoint/profile"))))
        self.write_fixture()
        self.fail_inputs("nested_profile")

    def test_truncated_xml(self):
        self.write_fixture(b"<device_data>")
        self.fail_inputs("invalid_xml")

    def test_utf16_entity_declaration(self):
        self.write_fixture('<!DOCTYPE device_data [<!ENTITY x "123">]><device_data/>'.encode("utf-16"))
        self.fail_inputs("xml_declarations_forbidden")

    def test_profile_path_injection(self):
        self.root.find("endpoint/profile").set("type", "../../evil")
        self.write_fixture()
        self.fail_inputs("invalid_profile_name")

    def test_external_reference(self):
        self.root.find("endpoint/profile").set("href", "/etc/passwd")
        self.write_fixture()
        self.fail_inputs("external_reference")

    def test_escaping_constant_reference(self):
        self.root.find("endpoint/profile/tuning-cp/ieq-amount").set("preset", "../../secret")
        self.write_fixture()
        self.fail_inputs("invalid_constant_reference")

    def test_nonfinite_numeric(self):
        for raw in ("nan", "inf", "1e400", "99999999999"):
            self.root.find("endpoint/profile/tuning-cp/ieq-amount").set("value", raw)
            self.write_fixture()
            with self.subTest(raw=raw):
                self.fail_inputs("nonfinite_or_excessive_parameter")

    def test_input_size_limit(self):
        self.xml.write_bytes(b" " * (speaker.MAX_BYTES + 1))
        self.fail_inputs("input_too_large")

    def test_xml_complexity_limit(self):
        el = self.root
        for _ in range(speaker.MAX_DEPTH + 1):
            el = ET.SubElement(el, "deep")
        self.write_fixture()
        self.fail_inputs("xml_complexity_limit")

    def test_input_symlink(self):
        link = self.path / "linked.xml"
        link.symlink_to(self.xml)
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.read_file(link)
        self.assertEqual(cm.exception.reason, "symlink_path")

    def test_input_fifo_nonblocking(self):
        fifo = self.path / "fifo"
        os.mkfifo(fifo)
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.read_file(fifo)
        self.assertEqual(cm.exception.reason, "input_not_regular")

    def test_duplicate_independent_input(self):
        other = self.path / "duplicate.xml"
        other.write_bytes(self.xml.read_bytes())
        self.assertEqual(speaker.inputs(self.arguments(duplicate_xml=other))[2]["duplicate_xml"], "byte-identical")
        other.write_bytes(b"disagree")
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.inputs(self.arguments(duplicate_xml=other))
        self.assertEqual(cm.exception.reason, "duplicate_xml_disagrees")

    def test_unknown_fields_visible(self):
        report = speaker.field_report(self.root.find("endpoint/profile"), self.root, [])
        row = next(x for x in report["fields"] if "unknown-future-stage" in x["source"])
        self.assertEqual(row["status"], "unsupported")
        self.assertFalse(report["complete_equivalence"])

    def test_unknown_optimizer_children_are_not_claimed_mapped(self):
        prof = self.root.find("endpoint/profile")
        ET.SubElement(prof.find("tuning-vlldp/audio-optimizer-bands"), "future-field", value="1")
        report = speaker.field_report(prof, self.root, [])
        self.assertEqual(next(x for x in report["fields"] if "future-field" in x["source"])["status"],
                         "unsupported")

    def test_inventory_is_read_once(self):
        real_read = speaker.read_file
        calls = []
        def read(path, *args):
            if path == self.inventory:
                calls.append(path)
            return real_read(path, *args)
        with mock.patch.object(speaker, "read_file", side_effect=read):
            speaker.inputs(self.arguments())
        self.assertEqual(len(calls), 1)

    def test_compressor_uses_grid_index_and_signed_q4_makeup(self):
        tuning = type("Tuning", (), dict(freqs=FREQS, ao_left=[0]*20, ao_right=[0]*20,
            curves={"ieq_balanced": [0]*20}, ieq_amount=10, peq_filters=[],
            vol_leveler=None, dialog_enhancer=None, mb_comp={"group_count": 1,
            "band_groups": [[20, -160, 16000, 16000, 16000, 0], [0, 0, 0, 0, 0, 0]]}))()
        speaker.validate_tuning(tuning)

    def test_unknown_enabled_peq_refused(self):
        prof = self.root.find("endpoint/profile")
        filters = ET.SubElement(prof.find("tuning-vlldp"), "speaker-peq-filters")
        ET.SubElement(filters, "filter", type="999", enabled="1", speaker="0", f0="1000")
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.validate_selected_profile(prof)
        self.assertEqual(cm.exception.reason, "unsupported_peq_filter")

    def test_error_does_not_echo_private_path(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            rc = speaker.main(["verify", "--bundle", str(self.path / "secret-address")])
        self.assertEqual(rc, 2)
        self.assertNotIn("secret-address", out.getvalue())

    def test_inspect_exclusive_private_report(self):
        argv = ["inspect", "--xml", str(self.xml), "--inf", str(self.inf),
                "--inventory", str(self.inventory), "--report", str(self.path / "report.json")]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(speaker.main(argv), 0)
            self.assertEqual(speaker.main(argv), 2)
        self.assertEqual((self.path / "report.json").stat().st_mode & 0o777, 0o600)


@unittest.skipUnless(os.environ.get("ROG_SPEAKER_CONVERTER"),
                     "set ROG_SPEAKER_CONVERTER to explicit pinned source; no OEM discovery")
class DSPPreparationTest(unittest.TestCase):
    setUp = PreparationTest.setUp
    write_fixture = PreparationTest.write_fixture
    arguments = PreparationTest.arguments
    def make(self, **changes):
        return speaker.build(self.arguments("build", **changes))

    def test_build_verify_deterministic(self):
        self.make()
        speaker.verify(self.path / "bundle")
        self.make(output=self.path / "bundle2")
        for f in (self.path / "bundle").rglob("*"):
            if f.is_file():
                self.assertEqual(f.read_bytes(), (self.path / "bundle2" / f.relative_to(self.path / "bundle")).read_bytes())

    def test_stereo_units_and_headroom(self):
        self.make()
        from scipy.io import wavfile
        import numpy as np
        manifest = json.loads((self.path / "bundle/manifest.json").read_text())
        rate, taps = wavfile.read(self.path / "bundle" / manifest["impulse"])
        self.assertEqual(rate, 48000)
        self.assertEqual(taps.shape, (4096, 2))
        # +1 dB left, -1 dB right; IEQ 1 dB * 10% common contribution.
        self.assertAlmostEqual(float(taps[:, 0].sum()), 1, places=6)
        self.assertAlmostEqual(float(taps[:, 1].sum()), 10 ** (-2/20), places=6)
        report = json.loads((self.path / "bundle/field-mapping.json").read_text())
        self.assertAlmostEqual(report["signal_checks"]["fir_attenuation_db"], 1.1, places=6)
        self.assertTrue(np.isfinite(taps).all())
        self.assertEqual(report["signal_checks"]["sweep_samples_over_full_scale"], 0)

    def test_all_cut_curve_is_never_boosted(self):
        for p in self.root.findall("endpoint/profile"):
            p.find("tuning-vlldp/audio-optimizer-bands/ch_00").set("value", ",".join(["-32"] * 20))
        self.write_fixture()
        self.make()
        report = json.loads((self.path / "bundle/field-mapping.json").read_text())
        self.assertEqual(report["signal_checks"]["fir_attenuation_db"], 0)

    def test_off_disables_ieq_and_optimizer(self):
        self.make(profile="off")
        report = json.loads((self.path / "bundle/field-mapping.json").read_text())
        self.assertAlmostEqual(report["signal_checks"]["fir_attenuation_db"], 0, places=6)

    def test_no_session_commands_or_socket_access(self):
        fake = self.path / "session"
        fake.mkdir()
        marker = fake / "sentinel"
        marker.write_text("stock routing")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(sock.close)
        sock.bind(str(fake / "easyeffects"))
        sock.listen(1)
        commands = self.path / "commands"
        commands.mkdir()
        log = self.path / "command-recorder"
        for command in ("systemctl", "wpctl", "pactl", "easyeffects", "pw-play", "aplay", "pw-metadata"):
            script = commands / command
            script.write_text("#!/bin/sh\nprintf '%s\\n' 'called' >> '" + str(log) + "'\nexit 99\n")
            script.chmod(0o700)
        with mock.patch.dict(os.environ, {"PATH": str(commands), "XDG_RUNTIME_DIR": str(fake),
                             "XDG_CONFIG_HOME": str(fake), "XDG_DATA_HOME": str(fake)}), \
             mock.patch("subprocess.Popen", side_effect=AssertionError("external command attempted")), \
             mock.patch.object(socket.socket, "connect", side_effect=AssertionError("socket attempted")):
            self.make()
        self.assertFalse(log.exists())
        self.assertEqual(marker.read_text(), "stock routing")
        self.assertEqual({p.name for p in fake.iterdir()}, {"sentinel", "easyeffects"})

    def test_output_symlink_and_overwrite_refused(self):
        out = self.path / "bundle"
        out.symlink_to(self.path, target_is_directory=True)
        with self.assertRaises(speaker.ProfileError):
            self.make()
        out.unlink()
        self.make()
        before = (out / "manifest.json").read_bytes()
        with self.assertRaises(speaker.ProfileError):
            self.make()
        self.assertEqual(before, (out / "manifest.json").read_bytes())

    def test_bundle_hash_tamper(self):
        self.make()
        (self.path / "bundle/preset.json").write_text("{}")
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.verify(self.path / "bundle")
        self.assertEqual(cm.exception.reason, "output_hash_mismatch")

    def test_bundle_missing_impulse(self):
        self.make()
        next((self.path / "bundle/irs").iterdir()).unlink()
        with self.assertRaises(speaker.ProfileError):
            speaker.verify(self.path / "bundle")

    def test_manifest_escaping_reference(self):
        self.make()
        path = self.path / "bundle/manifest.json"
        m = json.loads(path.read_text())
        m["outputs"]["../../outside"] = m["outputs"].pop("preset.json")
        path.write_bytes(speaker.json_bytes(m))
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.verify(self.path / "bundle")
        self.assertEqual(cm.exception.reason, "invalid_bundle_reference")

    def test_manifest_wrong_kernel_reference(self):
        self.make()
        p = self.path / "bundle/preset.json"
        preset = json.loads(p.read_text())
        preset["output"]["convolver#0"]["kernel-name"] = "outside"
        p.write_bytes(speaker.json_bytes(preset))
        m = self.path / "bundle/manifest.json"
        manifest = json.loads(m.read_text())
        manifest["outputs"]["preset.json"] = speaker.digest(p.read_bytes())
        m.write_bytes(speaker.json_bytes(manifest))
        with self.assertRaises(speaker.ProfileError) as cm:
            speaker.verify(self.path / "bundle")
        self.assertEqual(cm.exception.reason, "invalid_kernel_reference")

    def test_converter_modified_source_refused(self):
        source = self.path / "converter"
        source.mkdir()
        (source / "lib").mkdir()
        (source / "lib/__init__.py").write_text("raise Exception('not called')")
        with self.assertRaises(speaker.ProfileError) as cm:
            self.make(converter=source)
        self.assertEqual(cm.exception.reason, "converter_source_hash_mismatch")
        self.assertFalse((self.path / "bundle").exists())


if __name__ == "__main__":
    unittest.main()
