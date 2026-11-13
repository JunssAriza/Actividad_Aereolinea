"""
API REST asincrona para administrar paquetes de una agencia de viajes.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import coleccion_paquetes, verificar_conexion
from models import (
    PaqueteTuristico,
    PaqueteTuristicoCreate,
    PaqueteTuristicoUpdate,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    await verificar_conexion()
    yield


app = FastAPI(
    title="API Agencia de Viajes",
    description="API REST asincrona para administrar paquetes turisticos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAQUETE_FIELDS = (
    "destino",
    "duracion_dias",
    "precio_persona",
    "cupo_disponible",
)


async def _buscar_paquete_duplicado(
    datos: dict[str, Any], excluir_id: Optional[ObjectId] = None
) -> bool:
    filtro = {campo: datos[campo] for campo in PAQUETE_FIELDS}
    if excluir_id is not None:
        filtro["_id"] = {"$ne": excluir_id}
    return await coleccion_paquetes.find_one(filtro) is not None


@app.get("/", tags=["Raiz"])
async def root() -> dict[str, str]:
    return {
        "mensaje": "Bienvenido a la API de la Agencia de Viajes",
        "documentacion": "/docs",
    }


@app.post(
    "/paquetes",
    response_model=PaqueteTuristico,
    status_code=status.HTTP_201_CREATED,
    tags=["Paquetes turisticos"],
    summary="Crear un paquete turistico",
)
async def create_paquete(paquete_in: PaqueteTuristicoCreate) -> Any:
    datos_paquete = paquete_in.model_dump()
    if await _buscar_paquete_duplicado(datos_paquete):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un paquete turistico con esos mismos datos.",
        )

    datos_paquete["fecha_creacion"] = datetime.now(timezone.utc)
    resultado = await coleccion_paquetes.insert_one(datos_paquete)
    paquete_creado = await coleccion_paquetes.find_one(
        {"_id": resultado.inserted_id}
    )
    if paquete_creado is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El paquete se inserto, pero no fue posible recuperarlo.",
        )
    return paquete_creado


@app.get(
    "/paquetes",
    response_model=list[PaqueteTuristico],
    status_code=status.HTTP_200_OK,
    tags=["Paquetes turisticos"],
    summary="Listar paquetes turisticos",
)
async def get_paquetes() -> list[dict[str, Any]]:
    paquetes = []
    cursor = coleccion_paquetes.find()
    async for documento in cursor:
        paquetes.append(documento)
    return paquetes


@app.get(
    "/paquetes/{id}",
    response_model=PaqueteTuristico,
    status_code=status.HTTP_200_OK,
    tags=["Paquetes turisticos"],
    summary="Buscar un paquete por su ObjectId",
)
async def get_paquete_por_id(id: str) -> Any:
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ID '{id}' no es un ObjectId valido de MongoDB.",
        )

    paquete = await coleccion_paquetes.find_one({"_id": ObjectId(id)})
    if paquete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el paquete turistico con ID '{id}'.",
        )
    return paquete


@app.put(
    "/paquetes/{id}",
    response_model=PaqueteTuristico,
    status_code=status.HTTP_200_OK,
    tags=["Paquetes turisticos"],
    summary="Actualizar parcialmente un paquete turistico",
)
async def update_paquete(id: str, paquete_update: PaqueteTuristicoUpdate) -> Any:
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ID '{id}' no es un ObjectId valido de MongoDB.",
        )

    datos_a_actualizar = paquete_update.model_dump(exclude_unset=True)
    if not datos_a_actualizar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos un campo para actualizar.",
        )

    object_id = ObjectId(id)
    paquete_existente = await coleccion_paquetes.find_one({"_id": object_id})
    if paquete_existente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el paquete turistico con ID '{id}'.",
        )

    paquete_resultante = {**paquete_existente, **datos_a_actualizar}
    if await _buscar_paquete_duplicado(paquete_resultante, excluir_id=object_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe otro paquete turistico con esos mismos datos.",
        )

    resultado = await coleccion_paquetes.update_one(
        {"_id": object_id}, {"$set": datos_a_actualizar}
    )
    if resultado.matched_count != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el paquete turistico con ID '{id}'.",
        )

    paquete_actualizado = await coleccion_paquetes.find_one({"_id": object_id})
    if paquete_actualizado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el paquete turistico con ID '{id}'.",
        )
    return paquete_actualizado


@app.delete(
    "/paquetes/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Paquetes turisticos"],
    summary="Eliminar un paquete turistico",
)
async def delete_paquete(id: str) -> dict[str, str]:
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ID '{id}' no es un ObjectId valido de MongoDB.",
        )

    resultado = await coleccion_paquetes.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el paquete turistico con ID '{id}'.",
        )
    return {"mensaje": f"Paquete turistico con ID '{id}' eliminado correctamente."}