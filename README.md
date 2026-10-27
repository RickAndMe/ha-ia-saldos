# Saldos de IA para Home Assistant

Integración personalizada para Home Assistant que muestra, como sensores nativos,
el **crédito disponible en OpenRouter** y el **saldo de DeepSeek**.

Sin dependencias externas, sin scripts y sin nada corriendo fuera de Home Assistant:
la consulta la hace la propia integración cada 30 minutos.

## Instalación

1. HACS → Integraciones → menú → **Repositorios personalizados**.
2. Añade `https://github.com/RickAndMe/ha-ia-saldos` con categoría **Integration**.
3. Instálala y reinicia Home Assistant.
4. Ajustes → Dispositivos y servicios → **Añadir integración** → «Saldos de IA».
5. Pega la clave de OpenRouter, la de DeepSeek, o las dos.

## Sensores

**OpenRouter**

| Sensor | Qué es |
|---|---|
| Crédito de la clave | Lo que te queda gastable según el límite de la clave. **Es el que te limita de verdad.** |
| Saldo de la cuenta | Créditos comprados menos gasto acumulado. |
| Límite de la clave | Tope configurado en esa clave. |
| Gastado hoy / este mes / histórico | Consumo por periodo. |
| Créditos comprados | Total recargado histórico. |

**DeepSeek**

| Sensor | Qué es |
|---|---|
| Saldo | Saldo total disponible. |
| Saldo recargado | Parte que viene de recargas. |
| Saldo de regalo | Parte gratuita. |

## Detalles

- **Cada 30 minutos**, con reintento automático.
- Si una de las dos APIs falla, los sensores de la otra **siguen funcionando**; solo
  los del servicio caído pasan a `unavailable`.
- La clave se rechaza en el alta si la API no responde 200, así que no se guarda una
  clave mal escrita.
- Todo se configura desde la interfaz.

## API utilizada

- OpenRouter: `GET /api/v1/credits` y `GET /api/v1/key`
- DeepSeek: `GET /user/balance`

## Licencia

MIT
