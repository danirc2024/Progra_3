from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import asc
from modelos import Personaje, Mision, MisionPersonaje

# Importamos la cola directamente
from TDA_Cola import ArrayQueue

def obtener_cola_misiones(db: Session, personaje_id: int):
    """
    Obtiene la cola de misiones de un personaje ordenadas por FIFO (orden).
    """
    # Verificar si el personaje existe
    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    # Obtener las misiones ordenadas por FIFO (campo 'orden')
    misiones_rel = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id
    ).order_by(asc(MisionPersonaje.orden)).all()
    
    # Obtener las misiones completas
    misiones = []
    for rel in misiones_rel:
        mision = db.query(Mision).filter(Mision.id == rel.mision_id).first()
        if mision:
            misiones.append(mision)
    
    return misiones

def agregar_mision_a_cola(db: Session, personaje_id: int, mision_id: int):
    """
    Implementa la funcionalidad de enqueue() del TDA Cola a nivel de base de datos.
    """
    # Verificar si el personaje existe
    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    # Verificar si la misión existe
    mision = db.query(Mision).filter(Mision.id == mision_id).first()
    if not mision:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    # Verificar si la misión ya está asignada al personaje
    existente = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id,
        MisionPersonaje.mision_id == mision_id
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="Esta misión ya está asignada a este personaje")
    
    # Obtener el último orden
    max_orden = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id
    ).count()
    
    # Crear la relación
    nueva_asignacion = MisionPersonaje(
        personaje_id=personaje_id,
        mision_id=mision_id,
        orden=max_orden
    )
    
    db.add(nueva_asignacion)
    db.commit()
    
    return nueva_asignacion

def completar_primera_mision(db: Session, personaje_id: int):
    """
    Implementa la funcionalidad de dequeue() del TDA Cola a nivel de base de datos.
    """
    # Verificar si el personaje existe
    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    # Obtener la primera misión en la cola (la de menor orden)
    primera_mision_rel = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id
    ).order_by(asc(MisionPersonaje.orden)).first()
    
    if not primera_mision_rel:
        raise HTTPException(status_code=404, detail="El personaje no tiene misiones pendientes")
    
    # Obtener la misión
    mision = db.query(Mision).filter(Mision.id == primera_mision_rel.mision_id).first()
    if not mision:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    # Actualizar la experiencia del personaje
    personaje.experiencia += mision.experiencia
    
    # Actualizar el estado de la misión
    mision.estado = "completada"
    
    # Eliminar la relación
    db.delete(primera_mision_rel)
    
    # Actualizar el orden de las demás misiones
    otras_misiones = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id,
        MisionPersonaje.orden > primera_mision_rel.orden
    ).all()
    
    for rel in otras_misiones:
        rel.orden -= 1
    
    db.commit()
    
    return {
        "message": f"Misión '{mision.nombre}' completada",
        "experiencia_ganada": mision.experiencia,
        "experiencia_total": personaje.experiencia
    }

def crear_cola_en_memoria_desde_bd(db: Session, personaje_id: int):
    """
    Crea una cola en memoria usando el TDA ArrayQueue a partir de las misiones
    de un personaje en la base de datos.
    """
    # Obtener las misiones ordenadas
    misiones_ordenadas = obtener_cola_misiones(db, personaje_id)
    
    # Crear una nueva cola
    cola = ArrayQueue()
    
    # Añadir cada misión a la cola
    for mision in misiones_ordenadas:
        cola.enqueue(mision)
    
    return cola