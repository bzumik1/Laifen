"""Diagnostics for the Laifen integration."""

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .coordinator import LaifenConfigEntry

TO_REDACT = {CONF_ADDRESS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LaifenConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    toothbrush = entry.runtime_data.toothbrush
    state = toothbrush.state
    firmware_version_raw = toothbrush.firmware_version_raw
    last_session = toothbrush.last_session
    return {
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "connected": toothbrush.connected,
        "firmware_version": toothbrush.firmware_version,
        "firmware_version_raw": (
            firmware_version_raw.hex() if firmware_version_raw else None
        ),
        "state": (
            {
                **asdict(state),
                "mode": state.mode.name,
                "mode_settings": {
                    mode.name: asdict(settings)
                    for mode, settings in state.mode_settings.items()
                },
            }
            if state
            else None
        ),
        "last_session": asdict(last_session) if last_session else None,
    }
