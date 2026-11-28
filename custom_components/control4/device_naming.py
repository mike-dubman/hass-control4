"""Naming rules for generic Control4 Dynalite parent devices."""

from collections.abc import Iterable, Mapping
from typing import Any


GENERIC_DYNALITE_DEVICE_NAMES = frozenset(
    {"Dynalite Switch", "Dynalite Dimmer", "Dynalite Blinds"}
)


def single_entity_dynalite_name(
    parent_name: str | None,
    parent_id: int,
    item_id: int,
    items: Iterable[Mapping[str, Any]],
    entity_type: int,
) -> str | None:
    """Return the sole child name of a generic Dynalite parent, if unambiguous."""
    if parent_name not in GENERIC_DYNALITE_DEVICE_NAMES:
        return None

    children = [
        item
        for item in items
        if item.get("parentId") == parent_id and item.get("type") == entity_type
    ]
    if len(children) != 1 or children[0].get("id") != item_id:
        return None
    name = children[0].get("name")
    return name if isinstance(name, str) and name.strip() else None
