import asyncio
from datetime import datetime, UTC

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings


async def seed():
    """Inserta un documento de ejemplo si la base de datos está vacía."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    try:
        db = client[settings.mongodb_db_name]
        collection = db["documents"]

        # Verificar si ya hay datos para no duplicar
        count = await collection.count_documents({})
        if count > 0:
            print("ℹ️  Ya hay documentos en la base. Saltando seed.")
            return

        # Insertar documento de ejemplo
        await collection.insert_one(
            {
                "filename": "ejemplo.pdf",
                "content": "Este es un documento de prueba.",
                "checksum": "abc123def456",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

        print("✅ Seed completado: documento de ejemplo insertado.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed())