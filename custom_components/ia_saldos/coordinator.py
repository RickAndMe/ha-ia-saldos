"""Coordinador: uno por servicio, con su propio intervalo."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import CONSULTAS
from .const import DOMAIN, INTERVALO_DEBRID, INTERVALO_IA, SERVICIOS_IA

_LOGGER = logging.getLogger(__name__)


class ServicioCoordinator(DataUpdateCoordinator[dict]):
    """Consulta un único servicio y guarda su último resultado."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        servicio: str,
        clave: str,
    ) -> None:
        minutos = INTERVALO_IA if servicio in SERVICIOS_IA else INTERVALO_DEBRID
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{servicio}",
            update_interval=timedelta(minutes=minutos),
        )
        self.servicio = servicio
        self.servicio_minutos = minutos
        self._clave = clave
        self._sesion = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        return await CONSULTAS[self.servicio](self._sesion, self._clave)
