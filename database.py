from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

MONGODB_URL = config("MONGODB_URL", default="mongodb://localhost:27017")
DATABASE_NAME = config("DATABASE_NAME", default="Agencia_Viajes")

client = AsyncIOMotorClient(MONGODB_URL)

database = client[DATABASE_NAME]

coleccion_paquetes = database["paquetes_viajes"]


async def verificar_conexion() -> None:
    await client.admin.command("ping")
    print(f"Conexion exitosa a la base de datos: {DATABASE_NAME}")