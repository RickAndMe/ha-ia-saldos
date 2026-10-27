"""Constantes de la integración Saldos de IA."""

DOMAIN = "ia_saldos"

CONF_OPENROUTER = "openrouter_key"
CONF_DEEPSEEK = "deepseek_key"

OPENROUTER_SERVICIO = "openrouter"
DEEPSEEK_SERVICIO = "deepseek"

UPDATE_INTERVAL = 30  # minutos

URL_OPENROUTER_CREDITOS = "https://openrouter.ai/api/v1/credits"
URL_OPENROUTER_CLAVE = "https://openrouter.ai/api/v1/key"
URL_DEEPSEEK_SALDO = "https://api.deepseek.com/user/balance"

TIMEOUT = 25

NOMBRES_DISPOSITIVO = {
    OPENROUTER_SERVICIO: {
        "name": "OpenRouter",
        "manufacturer": "OpenRouter",
        "model": "Créditos de API",
    },
    DEEPSEEK_SERVICIO: {
        "name": "DeepSeek",
        "manufacturer": "DeepSeek",
        "model": "Plataforma",
    },
}
