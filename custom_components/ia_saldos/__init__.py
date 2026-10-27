"""Integración Saldos de IA: créditos de OpenRouter y DeepSeek dentro de Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IaSaldosCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Prepara la entrada de configuración."""
    coordinador = IaSaldosCoordinator(hass, entry)
    await coordinador.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinador
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_recarga_al_cambiar))
    return True


async def _recarga_al_cambiar(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descarga la entrada."""
    descargada = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if descargada:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return descargada
