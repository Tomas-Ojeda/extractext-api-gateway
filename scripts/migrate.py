import asyncio
from datetime import datetime, UTC

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings


async def migrate():
    """Aplica migraciones de datos a la colección de documentos."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    try:
        db = client[settings.mongodb_db_name]
        collection = db["documents"]

        # 1. Crear índice único en checksum si no existe
        await collection.create_index("checksum", unique=True)
        print("✅ Índice único en 'checksum' creado/verificado.")

        # 2. Migrar documentos que falten el campo 'updated_at'
        result = await collection.update_many(
            {"updated_at": {"$exists": False}},
            {"$set": {"updated_at": datetime.now(UTC)}},
        )
        print(f"✅ {result.modified_count} documento(s) migrado(s) con 'updated_at'.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(migrate())