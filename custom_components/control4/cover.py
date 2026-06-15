"""Platform for Control4 Covers (blinds/shades)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
	ATTR_POSITION,
	CoverEntity,
	CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyControl4.blind import C4Blind
from pyControl4.error_handling import C4Exception

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

# Fallback when director item capabilities are missing (lawtancool #71).
_POSITION_SET_SUPPORTED_DEVICE_MODELS: dict[str, set[str]] = {
	"qmotion": {
		"qadvanced roller shade",
	},
}

_MIN_COVER_LEVEL = 0
_MAX_COVER_LEVEL = 100

_VAR_LEVEL = "Level"
_VAR_FULLY_CLOSED = "Fully Closed"
_VAR_FULLY_OPEN = "Fully Open"
_VAR_OPENING = "Opening"
_VAR_CLOSING = "Closing"


def _attr_value(attributes: dict[str, Any], *keys: str) -> Any:
	"""Return the first matching attribute (exact or case-insensitive key)."""
	for key in keys:
		if key in attributes:
			return attributes[key]
	lower_map = {str(k).lower(): v for k, v in attributes.items()}
	for key in keys:
		if key.lower() in lower_map:
			return lower_map[key.lower()]
	return None


def _parse_cover_level(value: Any) -> int | None:
	"""Parse Control4 level (0-100) from director or websocket values."""
	if value is None:
		return None
	if isinstance(value, bool):
		return None
	if isinstance(value, int):
		level = value
	elif isinstance(value, float):
		level = int(value)
	elif isinstance(value, str) and value.strip().isdigit():
		level = int(value.strip())
	else:
		return None
	if _MIN_COVER_LEVEL <= level <= _MAX_COVER_LEVEL:
		return level
	return None


def _parse_service_position(value: Any) -> int | None:
	"""Parse HA cover.set_cover_position service argument."""
	if value is None or isinstance(value, bool):
		return None
	if isinstance(value, (int, float)):
		level = int(value)
	elif isinstance(value, str) and value.strip().isdigit():
		level = int(value.strip())
	else:
		return None
	if _MIN_COVER_LEVEL <= level <= _MAX_COVER_LEVEL:
		return level
	return None


def _parse_bool(value: Any) -> bool | None:
	"""Parse Control4 boolean variables."""
	if value is None:
		return None
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in ("true", "1", "yes"):
			return True
		if normalized in ("false", "0", "no"):
			return False
	return None


def _item_capabilities(item: dict[str, Any]) -> dict[str, Any]:
	caps = item.get("capabilities")
	return caps if isinstance(caps, dict) else {}


def _supports_set_position_allowlist(
	device_manufacturer: str | None, device_model: str | None
) -> bool:
	if not device_manufacturer or not device_model:
		return False
	if not isinstance(device_manufacturer, str) or not isinstance(device_model, str):
		return False
	return device_model.lower() in _POSITION_SET_SUPPORTED_DEVICE_MODELS.get(
		device_manufacturer.lower(), set()
	)


def _has_level_variable(attributes: dict[str, Any]) -> bool:
	"""True when the director exposes a Level variable for this blind."""
	return _attr_value(attributes, _VAR_LEVEL, "level") is not None


def _supports_set_position(
	item: dict[str, Any],
	device_manufacturer: str | None,
	device_model: str | None,
) -> bool:
	"""True when the driver accepts SET_LEVEL_TARGET (position slider)."""
	caps = _item_capabilities(item)
	if caps:
		return bool(caps.get("has_level")) and bool(caps.get("level_discrete_control"))
	return _supports_set_position_allowlist(device_manufacturer, device_model)


def _has_position_state(
	item: dict[str, Any],
	device_manufacturer: str | None,
	device_model: str | None,
	attributes: dict[str, Any],
) -> bool:
	"""True when level/open state can be read (polling), with or without a slider."""
	caps = _item_capabilities(item)
	if caps.get("has_level"):
		return True
	if _has_level_variable(attributes):
		return True
	return _supports_set_position_allowlist(device_manufacturer, device_model)


async def async_setup_entry(
	hass: HomeAssistant,
	entry: ConfigEntry,
	async_add_entities: AddEntitiesCallback,
) -> None:
	"""Set up Control4 covers from a config entry."""
	entry_data = hass.data[DOMAIN][entry.entry_id]
	all_items: list[dict[str, Any]] = entry_data[CONF_DIRECTOR_ALL_ITEMS]

	items_by_id = {item.get("id"): item for item in all_items if "id" in item}

	def _is_cover_proxy(proxy_value: str | None) -> bool:
		if not proxy_value or not isinstance(proxy_value, str):
			return False
		p = proxy_value.lower()
		return any(s in p for s in _COVER_PROXY_SUBSTRINGS)

	cover_items: list[dict[str, Any]] = [
		item
		for item in all_items
		if item.get("type") == CONTROL4_ENTITY_TYPE
		and item.get("id")
		and _is_cover_proxy(item.get("proxy"))
	]

	entity_list: list[Control4Cover] = []

	for item in cover_items:
		try:
			item_name = str(item["name"])
			item_id = item["id"]
			item_area = item.get("roomName")
			item_parent_id = item["parentId"]

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
		has_position_state = _has_position_state(
			item, item_manufacturer, item_model, item_attributes
		)
		supports_set_position = _supports_set_position(
			item, item_manufacturer, item_model
		)
		if has_position_state and not supports_set_position:
			_LOGGER.debug(
				"Cover %s (%s) reports level but driver has no discrete level control; "
				"open/close/stop only",
				item_name,
				item_id,
			)

		entity_list.append(
			Control4Cover(
				has_position_state,
				supports_set_position,
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


class Control4Cover(Control4Entity, CoverEntity):  # type: ignore[misc]
	"""Control4 cover (blinds/shades) entity."""

	def __init__(
		self,
		has_position_state: bool,
		supports_set_position: bool,
		entry_data: dict,
		entry: ConfigEntry,
		name: str,
		idx: int,
		device_name: str | None,
		device_manufacturer: str | None,
		device_model: str | None,
		device_id: int,
		device_area: str | None,
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
		self._has_position_state = has_position_state
		self._supports_set_position = supports_set_position
		features = (
			CoverEntityFeature.OPEN
			| CoverEntityFeature.CLOSE
			| CoverEntityFeature.STOP
		)
		if self._supports_set_position:
			features |= CoverEntityFeature.SET_POSITION
		self._attr_supported_features = features
		if self._supports_set_position and self._has_position_state:
			self._attr_should_poll = True
			self._attr_assumed_state = False
		elif self._has_position_state:
			# Report Level for UI display; assumed_state keeps Open/Close enabled
			# when level is partial (e.g. Dynalite stop mid-travel).
			self._attr_should_poll = True
			self._attr_assumed_state = True
		else:
			self._attr_should_poll = False
			self._attr_assumed_state = True

	def _report_position_state(self) -> bool:
		"""True when Level (and related vars) should map to HA cover state."""
		return self._has_position_state

	def create_api_object(self) -> C4Blind:
		"""Create a pyControl4 device object."""
		return C4Blind(self.entry_data[CONF_DIRECTOR], self._idx)

	async def async_added_to_hass(self):
		await super().async_added_to_hass()

	@property
	def current_cover_position(self) -> int | None:  # type: ignore[override]
		if not self._report_position_state():
			return None
		level = _parse_cover_level(
			_attr_value(self._extra_state_attributes, _VAR_LEVEL, "level")
		)
		if level is None:
			_LOGGER.debug(
				"Invalid or missing Level for cover %s (%s)",
				self._attr_name,
				self._idx,
			)
		return level

	@property
	def is_closed(self) -> bool | None:  # type: ignore[override]
		if not self._report_position_state():
			return None
		# Dynalite and similar drivers often leave flags at 0; only trust positive set.
		if _parse_bool(
			_attr_value(
				self._extra_state_attributes, _VAR_FULLY_CLOSED, "fully closed"
			)
		):
			return True
		if _parse_bool(
			_attr_value(
				self._extra_state_attributes, _VAR_FULLY_OPEN, "fully open"
			)
		):
			return False
		position = self.current_cover_position
		if position is None:
			return None
		return position == _MIN_COVER_LEVEL

	@property
	def is_closing(self) -> bool | None:  # type: ignore[override]
		if not self._report_position_state():
			return None
		return _parse_bool(
			_attr_value(self._extra_state_attributes, _VAR_CLOSING, "closing")
		)

	@property
	def is_opening(self) -> bool | None:  # type: ignore[override]
		if not self._report_position_state():
			return None
		return _parse_bool(
			_attr_value(self._extra_state_attributes, _VAR_OPENING, "opening")
		)

	async def _refresh_position_state(self) -> None:
		if not self._has_position_state:
			return
		await self.async_update()
		self.async_write_ha_state()

	async def async_open_cover(self, **kwargs: Any) -> None:
		c4_blind = self.create_api_object()
		await c4_blind.open()
		await self._refresh_position_state()

	async def async_close_cover(self, **kwargs: Any) -> None:
		c4_blind = self.create_api_object()
		await c4_blind.close()
		await self._refresh_position_state()

	async def async_set_cover_position(self, **kwargs: Any) -> None:
		if not self._supports_set_position:
			_LOGGER.debug(
				"Ignoring set_cover_position for %s (%s); driver has no level control",
				self._attr_name,
				self._idx,
			)
			return
		level = _parse_service_position(kwargs.get(ATTR_POSITION))
		if level is None:
			_LOGGER.warning(
				"Invalid cover position for %s (%s): %s",
				self._attr_name,
				self._idx,
				kwargs.get(ATTR_POSITION),
			)
			return
		c4_blind = self.create_api_object()
		try:
			await c4_blind.set_level_target(level=level)
		except C4Exception as err:
			_LOGGER.warning(
				"Control4 set_level_target failed for %s (%s): %s",
				self._attr_name,
				self._idx,
				err,
			)
			return
		await self._refresh_position_state()

	async def async_stop_cover(self, **kwargs: Any) -> None:
		c4_blind = self.create_api_object()
		await c4_blind.stop()
		await self._refresh_position_state()

	async def async_update(self) -> None:
		"""Poll director variables for covers that report level state."""
		if not self._has_position_state:
			return
		director = self.entry_data[CONF_DIRECTOR]
		data = await director.get_item_variables(self._idx)
		for item in data:
			self._extra_state_attributes[item["varName"]] = item["value"]
