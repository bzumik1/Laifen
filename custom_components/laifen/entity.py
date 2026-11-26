"""Base entity for the Laifen integration."""

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LaifenCoordinator


class LaifenEntity(CoordinatorEntity[LaifenCoordinator]):
    """Base class for Laifen entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LaifenCoordinator,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        address = coordinator.toothbrush.address
        self._attr_unique_id = f"{address}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            manufacturer="Laifen",
            model="Wave",
            model_id="LFTB01-P",
            name=coordinator.config_entry.title,
        )
