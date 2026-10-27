"""Integración Saldos de IA: créditos de IA y suscripciones debrid en Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CLAVES, DOMAIN
from .coordinator import ServicioCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Crea un coordinador por cada servicio con clave configurada."""
    coordinadores: dict[str, ServicioCoordinator] = {}
    datos = {**entry.data, **entry.options}

    for servicio, clave_conf in CLAVES.items():
        clave = (datos.get(clave_conf) or "").strip()
        if not clave:
            continue
        coordinador = ServicioCoordinator(hass, entry, servicio, clave)
        try:
            await coordinador.async_config_entry_first_refresh()
        except Exception as err:  # noqa: BLE001
            # Un servicio caído no debe impedir que arranquen los demás.
            _LOGGER.warning("No se pudo consultar %s: %s", servicio, err)
        coordinadores[servicio] = coordinador

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinadores
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
