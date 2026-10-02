#  API Gateway - extracText

Microservicio que actúa como **punto de entrada único** para todas las requests HTTP del sistema extracText.

## Responsabilidades

- Recibir todas las requests HTTP desde el exterior (a través de Traefik)
- Enrutar las requests a los microservicios correspondientes (Extractor y Storage)
- Manejar errores y respuestas HTTP
- Futuro: autenticación, rate limiting, logging centralizado

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.12 | Lenguaje principal |
| FastAPI | Framework web |
| httpx | Cliente HTTP async para comunicación entre microservicios |
| Uvicorn | Servidor ASGI |

## Estructura del Proyecto

```
api-gateway/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── documents.py   # Endpoints de documentos
│   │   │   └── health.py      # Health check
│   │   └── router.py          # Router principal
│   └── main.py                # Punto de entrada FastAPI
├── config/
│   └── settings.py            # Configuración con pydantic-settings
├── dockerfile
├── pyproject.toml
└── uv.lock
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/documents/` | Subir PDF, extraer texto y guardar |
| GET | `/api/v1/documents/` | Listar todos los documentos |
| GET | `/api/v1/documents/{id}` | Obtener documento por ID |
| PUT | `/api/v1/documents/{id}` | Actualizar contenido de documento |
| DELETE | `/api/v1/documents/{id}` | Eliminar documento |

## Variables de Entorno

| Variable | Descripción | Default |
|---|---|---|
| `APP_NAME` | Nombre de la aplicación | `extracText API Gateway` |
| `APP_VERSION` | Versión | `0.1.0` |
| `APP_DEBUG` | Modo debug | `false` |
| `EXTRACTOR_URL` | URL del microservicio Extractor | `http://pdf-extractxt-extractor:8000` |
| `STORAGE_URL` | URL del microservicio Storage | `http://pdf-extractxt-storage:8000` |

## Desarrollo Local

```bash
# Instalar dependencias
uv sync --all-extras

# Levantar servidor
uv run uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
# Construir imagen
docker build -f dockerfile -t extractext/api-gateway:latest .

# Levantar contenedor
docker run -p 8000:8000 extractext/api-gateway:latest
```
