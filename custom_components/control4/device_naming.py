"""Naming rules for Control4 devices with a single entity child."""

from collections.abc import Iterable, Mapping
from typing import Any


def single_entity_child_name(
    parent_id: int,
    item_id: int,
    items: Iterable[Mapping[str, Any]],
    device_type: int,
    entity_type: int,
) -> str | None:
    """Return the sole entity child name of a Control4 device, if unambiguous."""
    parent = None
    child = None
    for item in items:
        if item.get("id") == parent_id:
            parent = item
        if item.get("parentId") == parent_id and item.get("type") == entity_type:
            if child is not None:
                return None
            child = item
    if parent is None or parent.get("type") != device_type or child is None:
        return None
    if child.get("id") != item_id:
        return None
    name = child.get("name")
    return name if isinstance(name, str) and name.strip() else None
