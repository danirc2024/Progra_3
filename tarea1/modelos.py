from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Se define la base del modelo ORM
Base = declarative_base()

class Mision(Base):
    """
    Representa una misión dentro del juego.
    """
    __tablename__ = 'misiones'
    
    id = Column(Integer, primary_key=True)  # Identificador único de la misión
    nombre = Column(String(50), nullable=False)  # Nombre de la misión (obligatorio)
    descripcion = Column(Text, nullable=True)  # Descripción opcional de la misión
    experiencia = Column(Integer, default=0)  # XP de recompensa, por defecto 0
    estado = Column(Enum('pendiente', 'completada', name='estados'), nullable=False)  # Estado de la misión
    fecha_creacion = Column(DateTime, default=datetime.now)  # Fecha de creación con valor por defecto

    # Relación con MisionPersonaje
    personajes = relationship("MisionPersonaje", back_populates="mision")

class Personaje(Base):
    """
    Representa un personaje dentro del juego.
    """
    __tablename__ = 'personajes'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(30), nullable=False)
    experiencia = Column(Integer, default=0)  # Experiencia acumulada por el personaje
    misiones = relationship("MisionPersonaje", back_populates="personaje")
    
class MisionPersonaje(Base):
    """
    Tabla intermedia para la relación muchos a muchos entre Personaje y Mision.
    También permite manejar el orden FIFO de las misiones.
    """
    __tablename__ = 'misiones_personaje'
    
    personaje_id = Column(Integer, ForeignKey('personajes.id'), primary_key=True)
    mision_id = Column(Integer, ForeignKey('misiones.id'), primary_key=True)
    orden = Column(Integer)  # Para mantener el orden FIFO de las misiones

    # Relaciones inversas
    personaje = relationship("Personaje", back_populates="misiones")
    mision = relationship("Mision", back_populates="personajes")