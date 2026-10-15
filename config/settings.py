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
    ingestion_url: str = "http://pdf-extractxt-ingestion:8000"
    storage_url: str = "http://pdf-extractxt-storage:8000"

    # Timeouts de salida, en segundos (factor III)
    storage_timeout_seconds: int = 10
    ingestion_timeout_seconds: int = 45

    # Limite de carga de PDF (mismo valor que el extractor)
    pdf_max_size_mb: int = 10

    @property
    def pdf_max_size_bytes(self) -> int:
        return self.pdf_max_size_mb * 1024 * 1024


settings = Settings()
