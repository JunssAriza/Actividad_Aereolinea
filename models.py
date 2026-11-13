"""
Modelos Pydantic para la entidad PaqueteTuristico y el ObjectId de MongoDB.
"""

from datetime import datetime
from typing import Annotated, Any, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import core_schema


class _ObjectIdPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> Any:
        def validate(value: Any) -> str:
            if isinstance(value, ObjectId):
                return str(value)
            if isinstance(value, str) and ObjectId.is_valid(value):
                return value
            raise ValueError("ID invalido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=_handler(_source_type),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


PyObjectId = Annotated[str, _ObjectIdPydanticAnnotation]


class PaqueteTuristicoBase(BaseModel):
    destino: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Destino principal del paquete turistico",
        examples=["Cartagena"],
    )
    duracion_dias: int = Field(
        ...,
        gt=0,
        description="Duracion del viaje en dias",
        examples=[5],
    )
    precio_persona: float = Field(
        ...,
        gt=0,
        description="Precio del paquete por persona",
        examples=[1250000],
    )
    cupo_disponible: int = Field(
        ...,
        ge=0,
        description="Cantidad de cupos disponibles",
        examples=[12],
    )


class PaqueteTuristicoCreate(PaqueteTuristicoBase):
    pass


class PaqueteTuristico(PaqueteTuristicoBase):
    id: PyObjectId = Field(alias="_id")
    fecha_creacion: datetime

    model_config = ConfigDict(populate_by_name=True)


class PaqueteTuristicoUpdate(BaseModel):
    destino: Optional[str] = Field(None, min_length=3, max_length=120)
    duracion_dias: Optional[int] = Field(None, gt=0)
    precio_persona: Optional[float] = Field(None, gt=0)
    cupo_disponible: Optional[int] = Field(None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values: Any) -> Any:
        if isinstance(values, dict):
            null_fields = [name for name, value in values.items() if value is None]
            if null_fields:
                raise ValueError(
                    f"Los campos no pueden ser nulos: {', '.join(null_fields)}"
                )
        return values