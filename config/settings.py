from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada del API Gateway (12-factor: config desde entorno)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "extracText API Gateway"
    app_version: str = "0.1.0"
    app_debug: bool = False

    # URLs de los microservicios
    extractor_url: str = "http://pdf-extractxt-extractor:8000"
    storage_url: str = "http://pdf-extractxt-storage:8000"


settings = Settings()
