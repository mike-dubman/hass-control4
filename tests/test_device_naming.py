"""Tests for the dependency-free Control4 device naming guard."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "control4"
    / "device_naming.py"
)
SPEC = spec_from_file_location("control4_device_naming", MODULE_PATH)
assert SPEC and SPEC.loader
device_naming = module_from_spec(SPEC)
SPEC.loader.exec_module(device_naming)


class Control4DeviceNamingTest(unittest.TestCase):
    def test_single_entity_parent_uses_item_name(self):
        items = [
            {"id": 41, "type": 6, "name": "Dynalite Switch"},
            {"id": 42, "parentId": 41, "type": 7, "name": "Holiday off"},
            {"id": 43, "parentId": 41, "type": 3},
        ]
        self.assertEqual(
            device_naming.single_entity_child_name(41, 42, items, 6, 7),
            "Holiday off",
        )

    def test_shared_parent_keeps_original_device_name(self):
        items = [
            {"id": 41, "type": 6},
            {"id": 42, "parentId": 41, "type": 7},
            {"id": 43, "parentId": 41, "type": 7},
        ]
        self.assertIsNone(device_naming.single_entity_child_name(41, 42, items, 6, 7))

    def test_empty_child_name_does_not_replace_device_name(self):
        items = [
            {"id": 41, "type": 6},
            {"id": 42, "parentId": 41, "type": 7, "name": "Light"},
        ]
        items[1]["name"] = " "
        self.assertIsNone(device_naming.single_entity_child_name(41, 42, items, 6, 7))

    def test_missing_item_does_not_rename_parent(self):
        items = [{"id": 41, "type": 6}, {"id": 43, "parentId": 41, "type": 7}]
        self.assertIsNone(device_naming.single_entity_child_name(41, 42, items, 6, 7))

    def test_attribute_sensor_uses_the_same_child_device_name(self):
        items = [
            {"id": 41, "type": 6},
            {"id": 42, "parentId": 41, "type": 7, "name": "Garden light"},
        ]
        device_name = device_naming.single_entity_child_name(41, 42, items, 6, 7)
        self.assertEqual(device_name, "Garden light")
        self.assertNotEqual(device_name, "Power")

    def test_non_dynalite_parent_uses_same_rule(self):
        items = [
            {"id": 71, "type": 6, "name": "CoolMasterNet HVAC Zone"},
            {"id": 72, "parentId": 71, "type": 7, "name": "Salon AC"},
        ]
        self.assertEqual(
            device_naming.single_entity_child_name(71, 72, items, 6, 7),
            "Salon AC",
        )

    def test_room_parent_does_not_become_a_device_name(self):
        items = [
            {"id": 71, "type": 8, "name": "Living room"},
            {"id": 72, "parentId": 71, "type": 7, "name": "Remote Hub"},
        ]
        self.assertIsNone(device_naming.single_entity_child_name(71, 72, items, 6, 7))


if __name__ == "__main__":
    unittest.main()
