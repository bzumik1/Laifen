"""Coordinator for the Laifen integration."""

import logging
from typing import override

from laifen_ble import LaifenConnectionError, LaifenToothbrush

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
    async_register_advertisement_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

type LaifenConfigEntry = ConfigEntry[LaifenCoordinator]


class LaifenCoordinator(DataUpdateCoordinator[None]):
    """Connect to a Laifen toothbrush whenever it is awake.

    The toothbrush only advertises while it is awake and pushes its state over
    the connection, so connecting is triggered by its advertisements instead of
    by polling. Its advertisements never change, so every advertisement is
    watched, not only changed ones.
    """

    config_entry: LaifenConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: LaifenConfigEntry,
        toothbrush: LaifenToothbrush,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=toothbrush.name,
        )
        self.toothbrush = toothbrush

    @override
    async def _async_setup(self) -> None:
        """Listen to the toothbrush and to its advertisements."""
        self.config_entry.async_on_unload(
            self.toothbrush.register_callback(self.async_update_listeners)
        )
        self.config_entry.async_on_unload(
            async_register_advertisement_callback(
                self.hass, self._async_handle_advertisement, self.toothbrush.address
            )
        )

    @callback
    def _async_handle_advertisement(
        self, service_info: BluetoothServiceInfoBleak
    ) -> None:
        """Connect once the Bluetooth manager has stored the advertisement."""
        if not self.toothbrush.connected:
            self.hass.loop.call_soon(self._debounced_refresh.async_schedule_call)

    @override
    async def _async_update_data(self) -> None:
        """Connect to the toothbrush if it is awake."""
        if self.toothbrush.connected:
            return
        ble_device = async_ble_device_from_address(
            self.hass, self.toothbrush.address, connectable=True
        )
        if ble_device is None:
            return
        self.toothbrush.set_ble_device(ble_device)
        try:
            await self.toothbrush.connect()
        except LaifenConnectionError as err:
            _LOGGER.debug("Could not connect to %s: %s", self.toothbrush.name, err)
            return
        if self.toothbrush.firmware_version is not None:
            dr.async_get(self.hass).async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                connections={(CONNECTION_BLUETOOTH, self.toothbrush.address)},
                sw_version=self.toothbrush.firmware_version,
            )

    @override
    async def async_shutdown(self) -> None:
        """Disconnect from the toothbrush."""
        await super().async_shutdown()
        await self.toothbrush.disconnect()
