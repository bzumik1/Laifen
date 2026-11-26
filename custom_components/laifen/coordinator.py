"""Coordinator for the Laifen integration."""

import logging
from typing import override

from laifen_ble import LaifenConnectionError, LaifenToothbrush

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothCallbackReplay,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_address_present,
    async_register_callback,
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
    by polling.
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
            async_register_callback(
                self.hass,
                self._async_handle_advertisement,
                BluetoothCallbackMatcher(
                    address=self.toothbrush.address, connectable=True
                ),
                BluetoothScanningMode.PASSIVE,
                replay=BluetoothCallbackReplay.DISABLED,
            )
        )

    @callback
    def _async_handle_advertisement(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        """Connect when the toothbrush wakes up and advertises."""
        self.toothbrush.set_ble_device(service_info.device)
        if not self.toothbrush.connected:
            self._debounced_refresh.async_schedule_call()

    @override
    async def _async_update_data(self) -> None:
        """Connect to the toothbrush if it is awake."""
        if self.toothbrush.connected or not async_address_present(
            self.hass, self.toothbrush.address, connectable=True
        ):
            return
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
