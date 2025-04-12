from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List

from modelos import Personaje, Mision, MisionPersonaje
from base_datos import get_db, crear_base_datos
from esquemas import PersonajeCreate, MisionCreate, PersonajeOut, MisionOut
from gestor_cola import obtener_cola_misiones, agregar_mision_a_cola, completar_primera_mision

# Crear la base de datos si no existe
crear_base_datos()

app = FastAPI(title="Sistema de Misiones RPG con Colas",
              description="API para gestionar misiones en un juego RPG utilizando estructuras de datos tipo Cola (FIFO)")

# 1. Crear personaje
@app.post("/personajes", response_model=PersonajeOut, tags=["Personajes"])
def crear_personaje(personaje: PersonajeCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo personaje en el juego.
    """
    db_personaje = Personaje(nombre=personaje.nombre, experiencia=0)
    db.add(db_personaje)
    db.commit()
    db.refresh(db_personaje)
    return db_personaje

# 2. Crear misión
@app.post("/misiones", response_model=MisionOut, tags=["Misiones"])
def crear_mision(mision: MisionCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva misión en el juego.
    """
    db_mision = Mision(
        nombre=mision.nombre,
        descripcion=mision.descripcion,
        experiencia=mision.experiencia,
        estado="pendiente"
    )
    db.add(db_mision)
    db.commit()
    db.refresh(db_mision)
    return db_mision

# 3. Aceptar misión 
@app.post("/personajes/{personaje_id}/misiones/{mision_id}", status_code=201, tags=["Personajes"])
def aceptar_mision(
    personaje_id: int = Path(..., title="ID del personaje"),
    mision_id: int = Path(..., title="ID de la misión"),
    db: Session = Depends(get_db)
):
    """
    Asigna una misión a un personaje y la coloca al final de su cola de misiones (FIFO).
    """
    # Verificar si el personaje existe
    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if personaje is None:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    # Verificar si la misión existe
    mision = db.query(Mision).filter(Mision.id == mision_id).first()
    if mision is None:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    # Verificar si la misión ya está asignada al personaje
    existente = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id,
        MisionPersonaje.mision_id == mision_id
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="Esta misión ya está asignada a este personaje")
    
    # Usar el gestor de cola para agregar la misión a la cola
    agregar_mision_a_cola(db, personaje_id, mision_id)
    
    return {"message": f"Misión '{mision.nombre}' asignada al personaje '{personaje.nombre}'"}

# 4. Completar misión
@app.post("/personajes/{personaje_id}/completar", tags=["Personajes"])
def completar_mision(
    personaje_id: int = Path(..., title="ID del personaje"),
    db: Session = Depends(get_db)
):
    """
    Completa la primera misión en la cola (FIFO) del personaje, 
    la elimina de su lista y le otorga la experiencia correspondiente.
    """
    return completar_primera_mision(db, personaje_id)

# 5. Listar misiones en orden FIFO
@app.get("/personajes/{personaje_id}/misiones", response_model=List[MisionOut], tags=["Personajes"])
def listar_misiones_personaje(
    personaje_id: int = Path(..., title="ID del personaje"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las misiones de un personaje en orden FIFO (la primera misión asignada es la primera en completarse).
    """
    # Verificar si el personaje existe
    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if personaje is None:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    # Obtener las misiones ordenadas por el campo 'orden'
    misiones_queue = obtener_cola_misiones(db, personaje_id)
    
    return misiones_queue