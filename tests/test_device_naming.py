"""Tests for the dependency-free Dynalite device naming guard."""

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


class DynaliteDeviceNamingTest(unittest.TestCase):
    def test_single_entity_generic_parent_uses_item_name(self):
        items = [
            {"id": 41, "name": "Dynalite Switch"},
            {"id": 42, "parentId": 41, "type": 7, "name": "Holiday off"},
            {"id": 43, "parentId": 41, "type": 3},
        ]
        self.assertEqual(
            device_naming.single_entity_dynalite_name(
                "Dynalite Switch", 41, 42, items, 7
            ),
            "Holiday off",
        )

    def test_shared_parent_keeps_original_device_name(self):
        items = [
            {"id": 42, "parentId": 41, "type": 7},
            {"id": 43, "parentId": 41, "type": 7},
        ]
        self.assertIsNone(
            device_naming.single_entity_dynalite_name(
                "Dynalite Blinds", 41, 42, items, 7
            )
        )

    def test_non_generic_and_empty_names_keep_original_device_name(self):
        items = [{"id": 42, "parentId": 41, "type": 7, "name": "Light"}]
        for parent_name in ("Kitchen keypad", None):
            with self.subTest(parent_name=parent_name):
                self.assertIsNone(
                    device_naming.single_entity_dynalite_name(
                        parent_name, 41, 42, items, 7
                    )
                )

        items[0]["name"] = " "
        self.assertIsNone(
            device_naming.single_entity_dynalite_name(
                "Dynalite Dimmer", 41, 42, items, 7
            )
        )

    def test_missing_item_does_not_rename_parent(self):
        items = [{"id": 43, "parentId": 41, "type": 7}]
        self.assertIsNone(
            device_naming.single_entity_dynalite_name(
                "Dynalite Switch", 41, 42, items, 7
            )
        )

    def test_attribute_sensor_keeps_the_child_device_name(self):
        items = [{"id": 42, "parentId": 41, "type": 7, "name": "Garden light"}]
        device_name = device_naming.single_entity_dynalite_name(
            "Dynalite Dimmer", 41, 42, items, 7
        )
        self.assertEqual(device_name, "Garden light")
        self.assertNotEqual(device_name, "Power")


if __name__ == "__main__":
    unittest.main()
