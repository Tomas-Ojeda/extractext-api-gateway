"""Registro del servicio en Consul (service discovery + health check)."""
import json
import logging
import socket
import time
import urllib.request

from config.settings import settings

logger = logging.getLogger("uvicorn.error")

SERVICE_PORT = 8000
REGISTER_RETRIES = 5
RETRY_DELAY_SECONDS = 2


def _service_id() -> str:
    # El hostname del contenedor es unico, asi las 3 replicas de storage no se pisan.
    return f"{settings.service_name}-{socket.gethostname()}"


def _consul_put(path: str, body: dict | None = None) -> None:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{settings.consul_url}{path}",
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=3):
        pass


def register() -> None:
    """Registra este servicio en Consul. Nunca lanza excepciones: si Consul
    no responde, el servicio arranca igual."""
    address = socket.gethostbyname(socket.gethostname())
    payload = {
        "ID": _service_id(),
        "Name": settings.service_name,
        "Address": address,
        "Port": SERVICE_PORT,
        "Check": {
            "HTTP": f"http://{address}:{SERVICE_PORT}/api/v1/health",
            "Interval": "10s",
            "Timeout": "3s",
            "DeregisterCriticalServiceAfter": "1m",
        },
    }
    for attempt in range(1, REGISTER_RETRIES + 1):
        try:
            _consul_put("/v1/agent/service/register", payload)
            logger.info("Servicio %s registrado en Consul", _service_id())
            return
        except Exception as exc:
            logger.warning(
                "Consul no disponible (intento %s/%s): %s", attempt, REGISTER_RETRIES, exc
            )
            time.sleep(RETRY_DELAY_SECONDS)
    logger.warning("No se pudo registrar en Consul; el servicio continua sin registro")


def deregister() -> None:
    """Da de baja el servicio al apagarse (best effort)."""
    try:
        _consul_put(f"/v1/agent/service/deregister/{_service_id()}")
    except Exception as exc:
        logger.warning("No se pudo desregistrar de Consul: %s", exc)
