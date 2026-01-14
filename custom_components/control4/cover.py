"""Platform for Control4 Covers (blinds/shades)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
	CoverEntity,
	CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyControl4.blind import C4Blind

from . import Control4Entity
from .const import (
	CONF_DIRECTOR,
	CONF_DIRECTOR_ALL_ITEMS,
	CONTROL4_ENTITY_TYPE,
	DOMAIN,
)
from .director_utils import director_get_entry_variables

_LOGGER = logging.getLogger(__name__)

# Substrings commonly found in Control4 proxy identifiers for window coverings
_COVER_PROXY_SUBSTRINGS = (
	"shade",
	"blind",
	"windowcover",
	"curtain",
	"drap",
)


async def async_setup_entry(
	hass: HomeAssistant,
	entry: ConfigEntry,
	async_add_entities: AddEntitiesCallback,
) -> None:
	"""Set up Control4 covers from a config entry."""
	entry_data = hass.data[DOMAIN][entry.entry_id]
	all_items: list[dict[str, Any]] = entry_data[CONF_DIRECTOR_ALL_ITEMS]

	# Build quick lookup by id for parent data
	items_by_id = {item.get("id"): item for item in all_items if "id" in item}

	def _is_cover_proxy(proxy_value: str | None) -> bool:
		if not proxy_value or not isinstance(proxy_value, str):
			return False
		p = proxy_value.lower()
		return any(s in p for s in _COVER_PROXY_SUBSTRINGS)

	# Identify cover entities via proxy type heuristics
	cover_items: list[dict[str, Any]] = [
		item
		for item in all_items
		if item.get("type") == CONTROL4_ENTITY_TYPE
		and item.get("id")
		and _is_cover_proxy(item.get("proxy"))
	]
	_LOGGER.warning("Control4: discovered %d potential cover items", len(cover_items))

	entity_list: list[Control4Cover] = []

	for item in cover_items:
		try:
			item_name = str(item["name"])
			item_id = item["id"]
			item_area = item.get("roomName")
			item_parent_id = item.get("parentId")

			item_manufacturer = None
			item_device_name = None
			item_model = None

			parent = items_by_id.get(item_parent_id)
			if parent:
				item_manufacturer = parent.get("manufacturer")
				item_device_name = parent.get("name")
				item_model = parent.get("model")
		except KeyError:
			_LOGGER.exception(
				"Unknown device properties received from Control4: %s",
				item,
			)
			continue

		item_attributes = await director_get_entry_variables(hass, entry, item_id)

		entity_list.append(
			Control4Cover(
				entry_data,
				entry,
				item_name,
				item_id,
				item_device_name,
				item_manufacturer,
				item_model,
				item_parent_id,
				item_area,
				item_attributes,
			)
		)

	async_add_entities(entity_list, True)
	_LOGGER.warning("Control4: added %d cover entities", len(entity_list))


class Control4Cover(Control4Entity, CoverEntity):
	"""Control4 cover (blinds/shades) entity."""
	_attr_assumed_state = True
	_attr_supported_features = (
		CoverEntityFeature.OPEN
		| CoverEntityFeature.CLOSE
		| CoverEntityFeature.STOP
	)

	def __init__(
		self,
		entry_data: dict,
		entry: ConfigEntry,
		name: str,
		idx: int,
		device_name: str | None,
		device_manufacturer: str | None,
		device_model: str | None,
		device_id: int,
		device_area: str,
		device_attributes: dict,
	) -> None:
		super().__init__(
			entry_data,
			entry,
			name,
			idx,
			device_name,
			device_manufacturer,
			device_model,
			device_id,
			device_area,
			device_attributes,
		)
		# Keep covers usable even if websocket hasn't delivered state yet
		self._attr_available = True

	def create_api_object(self) -> C4Blind:
		"""Create a pyControl4 device object.
		This exists so the director token used is always the latest one,
		without needing to re-init the entire entity.
		"""
		return C4Blind(self.entry_data[CONF_DIRECTOR], self._idx)

	async def async_added_to_hass(self):
		await super().async_added_to_hass()

	@property
	def current_cover_position(self) -> int | None:
		"""Unknown in stateless mode to keep both buttons enabled."""
		return None

	@property
	def is_closed(self) -> bool | None:
		"""Unknown in stateless mode to keep both buttons enabled."""
		return None

	async def async_open_cover(self, **kwargs: Any) -> None:
		"""Open the cover."""
		c4_blind = self.create_api_object()
		# Some drivers respond better to explicit level targeting
		await c4_blind.setLevelTarget(100)

	async def async_close_cover(self, **kwargs: Any) -> None:
		"""Close the cover."""
		c4_blind = self.create_api_object()
		# Use explicit target to maximize compatibility
		await c4_blind.setLevelTarget(0)

	async def async_set_cover_position(self, **kwargs: Any) -> None:
		"""No-op in stateless mode (no position slider)."""
		return

	async def async_stop_cover(self, **kwargs: Any) -> None:
		"""Stop the cover."""
		c4_blind = self.create_api_object()
		await c4_blind.stop()

	@property
	def supported_features(self) -> int:
		"""Return supported features (stateless: no position slider)."""
		return (
			CoverEntityFeature.OPEN
			| CoverEntityFeature.CLOSE
			| CoverEntityFeature.STOP
		)

	async def _update_callback(self, device, message):
		"""Keep covers available regardless of websocket drops."""
		self._attr_available = True
		self.async_write_ha_state()
