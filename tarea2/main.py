# main.py
from fastapi import FastAPI, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# Importaciones locales
from database import get_db, crear_base_datos
from models import Vuelo, EstadoVuelo
from lista_vuelos import ListaVuelosPersistente

# Crear tablas en la base de datos
crear_base_datos()

app = FastAPI(title="Sistema de Gestión de Vuelos")

# Modelos Pydantic para la API
class VueloBase(BaseModel):
    codigo: str
    estado: str
    hora: Optional[datetime] = None
    origen: str
    destino: str

class VueloResponse(VueloBase):
    id: int
    
    class Config:
        from_attributes = True

class VueloCreate(VueloBase):
    emergencia: bool = False

class VueloInsert(VueloBase):
    posicion: int

class VueloReordenar(BaseModel):
    criterio: str  # "retraso", "hora", etc.

# Helpers
def crear_vuelo_db(vuelo_data: VueloBase, db: Session):
    db_vuelo = Vuelo(
        codigo=vuelo_data.codigo,
        estado=vuelo_data.estado,
        hora=vuelo_data.hora or datetime.now(),
        origen=vuelo_data.origen,
        destino=vuelo_data.destino
    )
    db.add(db_vuelo)
    db.commit()
    db.refresh(db_vuelo)
    return db_vuelo

# Endpoints de la API
@app.post("/vuelos", response_model=VueloResponse)
def añadir_vuelo(vuelo: VueloCreate, db: Session = Depends(get_db)):
    """Añade un vuelo al final (normal) o al frente (emergencia)."""
    # Crear el vuelo en la BD
    db_vuelo = crear_vuelo_db(vuelo, db)
    
    # Añadir a la lista enlazada
    lista = ListaVuelosPersistente(db)
    if vuelo.emergencia:
        lista.insertar_al_frente(db_vuelo)
    else:
        lista.insertar_al_final(db_vuelo)
    
    return db_vuelo

@app.get("/vuelos/total", response_model=int)
def obtener_total_vuelos(db: Session = Depends(get_db)):
    """Retorna el número total de vuelos en cola."""
    lista = ListaVuelosPersistente(db)
    return lista.longitud()

@app.get("/vuelos/proximo", response_model=VueloResponse)
def obtener_proximo_vuelo(db: Session = Depends(get_db)):
    """Retorna el primer vuelo sin remover."""
    lista = ListaVuelosPersistente(db)
    vuelo = lista.obtener_primero()
    if not vuelo:
        raise HTTPException(status_code=404, detail="No hay vuelos en la cola")
    return vuelo

@app.get("/vuelos/ultimo", response_model=VueloResponse)
def obtener_ultimo_vuelo(db: Session = Depends(get_db)):
    """Retorna el último vuelo sin remover."""
    lista = ListaVuelosPersistente(db)
    vuelo = lista.obtener_ultimo()
    if not vuelo:
        raise HTTPException(status_code=404, detail="No hay vuelos en la cola")
    return vuelo

@app.post("/vuelos/insertar", response_model=VueloResponse)
def insertar_vuelo_posicion(vuelo_data: VueloInsert, db: Session = Depends(get_db)):
    """Inserta un vuelo en una posición específica."""
    # Crear el vuelo en la BD
    db_vuelo = crear_vuelo_db(vuelo_data, db)
    
    # Insertar en la posición específica
    lista = ListaVuelosPersistente(db)
    try:
        lista.insertar_en_posicion(db_vuelo, vuelo_data.posicion)
    except IndexError:
        db.delete(db_vuelo)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Posición inválida: {vuelo_data.posicion}")
    
    return db_vuelo

@app.delete("/vuelos/extraer/{posicion}", response_model=VueloResponse)
def extraer_vuelo_posicion(posicion: int = Path(..., ge=0), db: Session = Depends(get_db)):
    """Remueve un vuelo de una posición dada."""
    lista = ListaVuelosPersistente(db)
    try:
        vuelo = lista.extraer_de_posicion(posicion)
        return vuelo
    except IndexError:
        raise HTTPException(status_code=404, detail=f"No existe vuelo en la posición {posicion}")

@app.get("/vuelos/lista", response_model=List[VueloResponse])
def listar_todos_vuelos(db: Session = Depends(get_db)):
    """Lista todos los vuelos en orden actual."""
    lista = ListaVuelosPersistente(db)
    return lista.obtener_lista_completa()

@app.patch("/vuelos/reordenar", response_model=List[VueloResponse])
def reordenar_vuelos(reorden: VueloReordenar, db: Session = Depends(get_db)):
    """Reordena manualmente la cola según un criterio."""
    lista = ListaVuelosPersistente(db)
    
    # Definir criterios de ordenamiento
    criterios = {
        "retraso": lambda v: v.estado == EstadoVuelo.RETRASADO.value,
        "hora": lambda v: v.hora,
        "emergencia": lambda v: v.estado != EstadoVuelo.EMERGENCIA.value,  # Emergencias primero
        "codigo": lambda v: v.codigo,
    }
    
    if reorden.criterio not in criterios:
        raise HTTPException(
            status_code=400, 
            detail=f"Criterio no válido. Opciones: {', '.join(criterios.keys())}"
        )
    
    lista.reordenar_por_criterio(criterios[reorden.criterio])
    return lista.obtener_lista_completa()