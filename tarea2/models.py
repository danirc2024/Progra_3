from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import datetime

Base = declarative_base()

class EstadoVuelo(enum.Enum):
    PROGRAMADO = "programado"
    EMERGENCIA = "emergencia"
    RETRASADO = "retrasado"

class Vuelo(Base):
    __tablename__ = "vuelos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    estado = Column(String, default=EstadoVuelo.PROGRAMADO.value)
    hora = Column(DateTime, default=datetime.datetime.now)
    origen = Column(String)
    destino = Column(String)
    
    # Relación con nodos para la lista enlazada
    nodo_id = Column(Integer, ForeignKey("nodos.id", ondelete="CASCADE"), nullable=True)
    nodo = relationship("Nodo", back_populates="vuelo", uselist=False)
    
    def __repr__(self):
        return f"<Vuelo {self.codigo}: {self.origen}->{self.destino}, {self.estado}>"
    
    def dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "estado": self.estado,
            "hora": self.hora.isoformat() if self.hora else None,
            "origen": self.origen,
            "destino": self.destino
        }

class Nodo(Base):
    __tablename__ = "nodos"
    
    id = Column(Integer, primary_key=True, index=True)
    anterior_id = Column(Integer, ForeignKey("nodos.id"), nullable=True)
    siguiente_id = Column(Integer, ForeignKey("nodos.id"), nullable=True)
    
    vuelo = relationship("Vuelo", back_populates="nodo")
    
    # Auto-relaciones para nodos anterior y siguiente
    anterior = relationship("Nodo", foreign_keys=[anterior_id], remote_side=[id], uselist=False)
    siguiente = relationship("Nodo", foreign_keys=[siguiente_id], remote_side=[id], uselist=False)

class ListaVuelos(Base):
    __tablename__ = "lista_vuelos"
    
    id = Column(Integer, primary_key=True, index=True)
    cabeza_id = Column(Integer, ForeignKey("nodos.id"), nullable=True)
    cola_id = Column(Integer, ForeignKey("nodos.id"), nullable=True)
    tamanio = Column(Integer, default=0)
    
    # Relaciones con los nodos cabeza y cola
    cabeza = relationship("Nodo", foreign_keys=[cabeza_id])
    cola = relationship("Nodo", foreign_keys=[cola_id])