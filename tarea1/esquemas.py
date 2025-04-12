from pydantic import BaseModel, Field
from typing import Optional

class PersonajeCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=30, example="Aragorn")

class PersonajeOut(BaseModel):
    id: int
    nombre: str
    experiencia: int
    
    class Config:
        from_attributes = True

class MisionCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, example="Derrotar al dragón")
    descripcion: Optional[str] = Field(None, example="Debes enfrentarte al temible dragón de la montaña")
    experiencia: int = Field(..., ge=0, example=100)

class MisionOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    experiencia: int
    estado: str
    
    class Config:
        from_attributes = True