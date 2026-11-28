"""Tests for the Control4 config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow

from custom_components.control4 import config_flow
from custom_components.control4.const import (
    CONF_CONTROLLER_UNIQUE_ID,
    DOMAIN,
)

CONTROLLER_UNIQUE_ID = "C4-SR260_C4-SR260_001122334455"

USER_INPUT = {
    config_flow._FORM_LABEL_HOST: "1.2.3.4",
    config_flow._FORM_LABEL_USERNAME: "user@example.com",
    config_flow._FORM_LABEL_PASSWORD: "hunter2",
}


async def _authenticate_ok(self):
    """Stand in for Control4Validator.authenticate that always succeeds."""
    self.controller_unique_id = CONTROLLER_UNIQUE_ID
    self.director_bearer_token = "token"
    return True


async def test_user_flow_success(hass):
    """A valid host/username/password creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch.object(config_flow.Control4Validator, "authenticate", _authenticate_ok),
        patch.object(
            config_flow.Control4Validator,
            "connect_to_director",
            AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.control4.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == CONTROLLER_UNIQUE_ID
    assert result["data"][CONF_CONTROLLER_UNIQUE_ID] == CONTROLLER_UNIQUE_ID


async def test_user_flow_invalid_auth(hass):
    """Bad credentials are surfaced as a form error, not an exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch.object(
            config_flow.Control4Validator,
            "authenticate",
            AsyncMock(return_value=False),
        ),
        patch.object(
            config_flow.Control4Validator,
            "connect_to_director",
            AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": config_flow._ERROR_INVALID_AUTH}


async def test_user_flow_cannot_connect(hass):
    """A network failure while authenticating is surfaced as a form error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch.object(
        config_flow.Control4Validator,
        "authenticate",
        AsyncMock(side_effect=config_flow.CannotConnect),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": config_flow._ERROR_CANNOT_CONNECT}


async def test_user_flow_already_configured(hass):
    """A second controller with the same MAC address aborts the flow."""
    with (
        patch.object(config_flow.Control4Validator, "authenticate", _authenticate_ok),
        patch.object(
            config_flow.Control4Validator,
            "connect_to_director",
            AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.control4.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        first = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        first = await hass.config_entries.flow.async_configure(
            first["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
        assert first["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        second = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        second = await hass.config_entries.flow.async_configure(
            second["flow_id"], USER_INPUT
        )

    assert second["type"] == data_entry_flow.FlowResultType.ABORT
    assert second["reason"] == config_flow._ABORT_ALREADY_CONFIGURED
