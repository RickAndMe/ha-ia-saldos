"""Consultas a las APIs externas."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    TIMEOUT,
    URL_ALDEBRID_USER,
    URL_DEEPSEEK_SALDO,
    URL_OPENROUTER_CLAVE,
    URL_OPENROUTER_CREDITOS,
    URL_REALDEBRID_USER,
    URL_TORBOX_USER,
)


async def _pide(sesion, url: str, clave: str) -> dict:
    """GET autenticado con Bearer. Lanza UpdateFailed si algo va mal."""
    cabeceras = {
        "Authorization": f"Bearer {clave}",
        "Accept": "application/json",
        "User-Agent": "hermes-ha-saldos/1.1",
    }
    try:
        async with asyncio.timeout(TIMEOUT):
            async with sesion.get(url, headers=cabeceras) as resp:
                if resp.status in (401, 403):
                    raise UpdateFailed("clave rechazada por la API")
                if resp.status != 200:
                    raise UpdateFailed(f"respuesta HTTP {resp.status}")
                return await resp.json(content_type=None)
    except asyncio.TimeoutError as err:
        raise UpdateFailed("la API no respondió a tiempo") from err


def _fecha(valor) -> datetime | None:
    """Convierte ISO 8601 o epoch a datetime con zona."""
    if not valor:
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(float(valor), tz=timezone.utc)
    try:
        texto = str(valor).replace("Z", "+00:00")
        fecha = datetime.fromisoformat(texto)
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return fecha
    except (ValueError, TypeError):
        return None


def _dias(fecha: datetime | None) -> int:
    if fecha is None:
        return 0
    return max(0, (fecha - datetime.now(timezone.utc)).days)


# ---------------------------------------------------------------- IA
async def lee_openrouter(sesion, clave: str) -> dict:
    creditos = (await _pide(sesion, URL_OPENROUTER_CREDITOS, clave)).get("data", {})
    datos_clave = (await _pide(sesion, URL_OPENROUTER_CLAVE, clave)).get("data", {})

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


async def lee_deepseek(sesion, clave: str) -> dict:
    crudo = await _pide(sesion, URL_DEEPSEEK_SALDO, clave)
    info = (crudo.get("balance_infos") or [{}])[0]
    return {
        "saldo": round(float(info.get("total_balance") or 0), 2),
        "recargado": round(float(info.get("topped_up_balance") or 0), 2),
        "regalo": round(float(info.get("granted_balance") or 0), 2),
        "operativo": bool(crudo.get("is_available")),
    }


# ---------------------------------------------------------------- DEBRID
async def lee_realdebrid(sesion, clave: str) -> dict:
    datos = await _pide(sesion, URL_REALDEBRID_USER, clave)
    tipo = str(datos.get("type") or "").lower()
    segundos = int(datos.get("premium") or 0)
    caduca = _fecha(datos.get("expiration"))
    return {
        "premium": tipo == "premium" and segundos > 0,
        "dias_restantes": _dias(caduca) if caduca else max(0, segundos // 86400),
        "caduca": caduca,
        "puntos": datos.get("points"),
        "usuario": datos.get("username"),
        "tipo_cuenta": tipo or "desconocido",
    }


async def lee_alldebrid(sesion, clave: str) -> dict:
    crudo = await _pide(sesion, URL_ALDEBRID_USER, clave)
    usuario = ((crudo.get("data") or {}).get("user")) or {}
    caduca = _fecha(usuario.get("premiumUntil"))
    return {
        "premium": bool(usuario.get("isPremium")),
        "dias_restantes": _dias(caduca),
        "caduca": caduca,
        "puntos": usuario.get("fidelityPoints"),
        "usuario": usuario.get("username"),
        "tipo_cuenta": (
            "trial" if usuario.get("isTrial")
            else ("suscripción" if usuario.get("isSubscribed") else "premium")
            if usuario.get("isPremium") else "gratis"
        ),
    }


async def lee_torbox(sesion, clave: str) -> dict:
    crudo = await _pide(sesion, URL_TORBOX_USER, clave)
    datos = crudo.get("data") or {}
    if isinstance(datos, list):  # algunas respuestas devuelven lista
        datos = datos[0] if datos else {}
    caduca = _fecha(datos.get("premium_expires_at"))
    return {
        "premium": bool(datos.get("is_subscribed")),
        "dias_restantes": _dias(caduca),
        "caduca": caduca,
        "usuario": datos.get("email") or datos.get("username"),
        "tipo_cuenta": str(datos.get("plan") or "desconocido"),
    }


CONSULTAS = {
    "openrouter": lee_openrouter,
    "deepseek": lee_deepseek,
    "realdebrid": lee_realdebrid,
    "alldebrid": lee_alldebrid,
    "torbox": lee_torbox,
}
