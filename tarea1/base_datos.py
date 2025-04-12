# base_datos.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelos import Base

# Creamos el motor de base de datos usando SQLite
motor = create_engine("sqlite:///rpg_misiones.db")

# Creamos la clase de sesión
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

def get_db():
    """
    Función para obtener una sesión de base de datos.
    Se usa como dependencia en FastAPI.
    """
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()

def crear_base_datos():
    """
    Crea todas las tablas en la base de datos si no existen.
    """
    Base.metadata.create_all(bind=motor)