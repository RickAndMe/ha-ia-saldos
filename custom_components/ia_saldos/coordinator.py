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
    CONF_PINGEN_ID,
    CONF_PINGEN_SECRET,
    DEEPSEEK_SERVICIO,
    DOMAIN,
    OPENROUTER_SERVICIO,
    PINGEN_SCOPE,
    PINGEN_SERVICIO,
    TIMEOUT,
    UPDATE_INTERVAL,
    URL_DEEPSEEK_SALDO,
    URL_OPENROUTER_CLAVE,
    URL_OPENROUTER_CREDITOS,
    URL_PINGEN_ORGANIZACIONES,
    URL_PINGEN_TOKEN,
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

    def _config(self, campo: str):
        """Las opciones mandan sobre los datos del alta."""
        return self.entry.options.get(campo) or self.entry.data.get(campo)

    async def _async_update_data(self) -> dict:
        datos: dict[str, dict] = {}
        errores: list[str] = []

        clave_or = self._config(CONF_OPENROUTER)
        clave_ds = self._config(CONF_DEEPSEEK)
        pingen_id = self._config(CONF_PINGEN_ID)
        pingen_secret = self._config(CONF_PINGEN_SECRET)

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
        if pingen_id and pingen_secret:
            try:
                datos[PINGEN_SERVICIO] = await self._pingen(pingen_id, pingen_secret)
            except Exception as err:  # noqa: BLE001
                errores.append(f"pingen: {err}")

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

    async def _pingen(self, client_id: str, client_secret: str) -> dict:
        """Pingen usa OAuth2 client_credentials: token y luego /organisations."""
        formulario = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": PINGEN_SCOPE,
        }
        async with asyncio.timeout(TIMEOUT):
            async with self._session.post(URL_PINGEN_TOKEN, data=formulario) as resp:
                if resp.status in (400, 401, 403):
                    raise UpdateFailed(
                        f"credenciales rechazadas ({resp.status})"
                    )
                if resp.status != 200:
                    raise UpdateFailed(f"token: respuesta HTTP {resp.status}")
                token = (await resp.json(content_type=None)).get("access_token")

        if not token:
            raise UpdateFailed("la API no devolvió access_token")

        cabeceras = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json",
        }
        async with asyncio.timeout(TIMEOUT):
            async with self._session.get(
                URL_PINGEN_ORGANIZACIONES, headers=cabeceras
            ) as resp:
                if resp.status == 401:
                    raise UpdateFailed("token rechazado (401)")
                if resp.status != 200:
                    raise UpdateFailed(f"organizaciones: respuesta HTTP {resp.status}")
                crudo = await resp.json(content_type=None)

        organizaciones = crudo.get("data") or []
        if isinstance(organizaciones, dict):
            organizaciones = [organizaciones]
        if not organizaciones:
            raise UpdateFailed("la cuenta no tiene organizaciones")

        org = organizaciones[0]
        attrs = org.get("attributes") or {}
        return {
            "saldo": round(float(attrs.get("billing_balance") or 0), 2),
            "moneda": attrs.get("billing_currency") or "",
            "faltante": round(float(attrs.get("missing_credits") or 0), 2),
            "plan": attrs.get("plan") or "desconocido",
            "organizacion": attrs.get("name") or org.get("id"),
            "estado": attrs.get("status") or "",
            "facturacion": attrs.get("billing_mode") or "",
        }
