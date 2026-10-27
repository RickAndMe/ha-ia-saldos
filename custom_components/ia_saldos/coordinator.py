"""Consulta periódica de los saldos de OpenRouter y DeepSeek."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEEPSEEK,
    CONF_OPENROUTER,
    DEEPSEEK_SERVICIO,
    DOMAIN,
    OPENROUTER_SERVICIO,
    TIMEOUT,
    UPDATE_INTERVAL,
    URL_DEEPSEEK_SALDO,
    URL_OPENROUTER_CLAVE,
    URL_OPENROUTER_CREDITOS,
)

_LOGGER = logging.getLogger(__name__)


class IaSaldosCoordinator(DataUpdateCoordinator):
    """Consulta las dos APIs y guarda el resultado."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        datos: dict[str, dict] = {}
        errores: list[str] = []

        clave_or = self.entry.data.get(CONF_OPENROUTER)
        clave_ds = self.entry.data.get(CONF_DEEPSEEK)

        if clave_or:
            try:
                datos[OPENROUTER_SERVICIO] = await self._openrouter(clave_or)
            except Exception as err:  # noqa: BLE001
                errores.append(f"openrouter: {err}")
        if clave_ds:
            try:
                datos[DEEPSEEK_SERVICIO] = await self._deepseek(clave_ds)
            except Exception as err:  # noqa: BLE001
                errores.append(f"deepseek: {err}")

        if not datos:
            raise UpdateFailed("; ".join(errores) or "no hay claves configuradas")
        if errores:
            _LOGGER.warning("Saldos de IA, consulta parcial: %s", "; ".join(errores))
        return datos

    async def _pide(self, url: str, clave: str) -> dict:
        cabeceras = {
            "Authorization": f"Bearer {clave}",
            "Accept": "application/json",
            "User-Agent": "hermes-ia-saldos/1.0",
        }
        async with asyncio.timeout(TIMEOUT):
            async with self._session.get(url, headers=cabeceras) as resp:
                if resp.status == 401:
                    raise UpdateFailed("clave rechazada (401)")
                if resp.status != 200:
                    raise UpdateFailed(f"respuesta HTTP {resp.status}")
                return await resp.json(content_type=None)

    async def _openrouter(self, clave: str) -> dict:
        creditos = (await self._pide(URL_OPENROUTER_CREDITOS, clave)).get("data", {})
        datos_clave = (await self._pide(URL_OPENROUTER_CLAVE, clave)).get("data", {})

        total = float(creditos.get("total_credits") or 0)
        usado = float(creditos.get("total_usage") or 0)

        return {
            "saldo_cuenta": round(total - usado, 2),
            "creditos_comprados": round(total, 2),
            "gastado_total": round(usado, 2),
            "credito_clave": round(float(datos_clave.get("limit_remaining") or 0), 2),
            "limite_clave": round(float(datos_clave.get("limit") or 0), 2),
            "gasto_hoy": round(float(datos_clave.get("usage_daily") or 0), 4),
            "gasto_mes": round(float(datos_clave.get("usage_monthly") or 0), 2),
        }

    async def _deepseek(self, clave: str) -> dict:
        crudo = await self._pide(URL_DEEPSEEK_SALDO, clave)
        info = (crudo.get("balance_infos") or [{}])[0]
        return {
            "saldo": round(float(info.get("total_balance") or 0), 2),
            "recargado": round(float(info.get("topped_up_balance") or 0), 2),
            "regalo": round(float(info.get("granted_balance") or 0), 2),
            "operativo": bool(crudo.get("is_available")),
        }
