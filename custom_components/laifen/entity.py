"""Base entities for the Laifen integration."""

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any, Concatenate, override

from laifen_ble import (
    LaifenCommandError,
    LaifenConnectionError,
    LaifenMotorError,
    LaifenToothbrush,
    LaifenValueError,
    MotorStatus,
)

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LaifenCoordinator

MOTOR_ERRORS = {
    MotorStatus.CHARGING: "charging",
    MotorStatus.LOW_BATTERY: "low_battery",
    MotorStatus.MALFUNCTION: "malfunction",
}


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
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, address)})

    @property
    def toothbrush(self) -> LaifenToothbrush:
        """Return the toothbrush."""
        return self.coordinator.toothbrush


class LaifenConnectedEntity(LaifenEntity):
    """Base class for entities that need a connected toothbrush."""

    @property
    @override
    def available(self) -> bool:
        """Return whether the toothbrush is connected."""
        return (
            super().available
            and self.toothbrush.connected
            and self.toothbrush.state is not None
        )


def _error_translation_key(err: LaifenCommandError) -> str:
    """Return the translation key for a refused command."""
    if isinstance(err, LaifenMotorError) and err.reason is not None:
        return MOTOR_ERRORS[err.reason]
    return "command_refused"


def laifen_command[_EntityT: LaifenEntity, **_P](
    func: Callable[Concatenate[_EntityT, _P], Awaitable[None]],
) -> Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, None]]:
    """Translate the errors of a toothbrush command."""

    @wraps(func)
    async def handler(self: _EntityT, *args: _P.args, **kwargs: _P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
        except LaifenValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="invalid_value"
            ) from err
        except LaifenConnectionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="communication_error"
            ) from err
        except LaifenCommandError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key=_error_translation_key(err),
            ) from err

    return handler
