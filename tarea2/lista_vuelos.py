# lista_vuelos.py
from models import Vuelo, Nodo, ListaVuelos
from sqlalchemy.orm import Session

class ListaVuelosPersistente:
    """
    Implementación de una lista doblemente enlazada que persiste los datos en SQLAlchemy.
    Gestiona vuelos mediante una estructura de nodos enlazados almacenados en base de datos.
    """
    def __init__(self, db: Session):
        """
        Inicializa una lista vacía o carga la existente desde la base de datos.
        
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db
        # Buscar si ya existe una lista en la BD
        lista_existente = db.query(ListaVuelos).first()
        if not lista_existente:
            # Crear nueva lista
            self.lista = ListaVuelos()
            db.add(self.lista)
            db.commit()
            db.refresh(self.lista)
        else:
            self.lista = lista_existente
    
    def longitud(self):
        """Retorna el número total de vuelos en la lista (O(1))."""
        return self.lista.tamanio
    
    def esta_vacia(self):
        """Retorna True si la lista está vacía (O(1))."""
        return self.lista.tamanio == 0
    
    def _crear_nodo(self, vuelo, anterior=None, siguiente=None):
        """
        Crea un nuevo nodo para un vuelo.
        
        Args:
            vuelo: Objeto Vuelo a insertar
            anterior: Nodo anterior
            siguiente: Nodo siguiente
            
        Returns:
            Nodo creado
        """
        nodo = Nodo()
        self.db.add(nodo)
        self.db.flush()  # Para obtener el ID del nodo
        
        # Asociar el vuelo con este nodo
        vuelo.nodo_id = nodo.id
        
        # Establecer referencias
        if anterior:
            nodo.anterior_id = anterior.id
            anterior.siguiente_id = nodo.id
        
        if siguiente:
            nodo.siguiente_id = siguiente.id
            siguiente.anterior_id = nodo.id
        
        self.db.flush()
        return nodo
    
    def _eliminar_nodo(self, nodo):
        """
        Elimina un nodo de la lista y devuelve su vuelo.
        
        Args:
            nodo: Nodo a eliminar
            
        Returns:
            Vuelo del nodo eliminado
        """
        if not nodo:
            raise ValueError("El nodo no existe")
            
        # Guardar referencia al vuelo
        vuelo = self.db.query(Vuelo).filter(Vuelo.nodo_id == nodo.id).first()
        
        # Reconectar nodos adyacentes
        if nodo.anterior_id:
            anterior = self.db.query(Nodo).get(nodo.anterior_id)
            anterior.siguiente_id = nodo.siguiente_id
        
        if nodo.siguiente_id:
            siguiente = self.db.query(Nodo).get(nodo.siguiente_id)
            siguiente.anterior_id = nodo.anterior_id
        
        # Actualizar cabeza o cola si es necesario
        if self.lista.cabeza_id == nodo.id:
            self.lista.cabeza_id = nodo.siguiente_id
        
        if self.lista.cola_id == nodo.id:
            self.lista.cola_id = nodo.anterior_id
        
        # Desasociar vuelo del nodo
        if vuelo:
            vuelo.nodo_id = None
        
        # Eliminar nodo
        self.db.delete(nodo)
        
        # Actualizar tamaño
        self.lista.tamanio -= 1
        self.db.flush()
        
        return vuelo
    
    def insertar_al_frente(self, vuelo):
        """
        Añade un vuelo al inicio de la lista (para emergencias) (O(1)).
        """
        if self.esta_vacia():
            nodo = self._crear_nodo(vuelo)
            self.lista.cabeza_id = nodo.id
            self.lista.cola_id = nodo.id
        else:
            cabeza = self.db.query(Nodo).get(self.lista.cabeza_id)
            nodo = self._crear_nodo(vuelo, siguiente=cabeza)
            self.lista.cabeza_id = nodo.id
        
        self.lista.tamanio += 1
        self.db.commit()
        return nodo
    
    def insertar_al_final(self, vuelo):
        """
        Añade un vuelo al final de la lista (vuelos regulares) (O(1)).
        """
        if self.esta_vacia():
            nodo = self._crear_nodo(vuelo)
            self.lista.cabeza_id = nodo.id
            self.lista.cola_id = nodo.id
        else:
            cola = self.db.query(Nodo).get(self.lista.cola_id)
            nodo = self._crear_nodo(vuelo, anterior=cola)
            self.lista.cola_id = nodo.id
        
        self.lista.tamanio += 1
        self.db.commit()
        return nodo
    
    def obtener_primero(self):
        """
        Retorna (sin remover) el primer vuelo de la lista (O(1))
        """
        if self.esta_vacia():
            return None
        
        nodo_cabeza = self.db.query(Nodo).get(self.lista.cabeza_id)
        return self.db.query(Vuelo).filter(Vuelo.nodo_id == nodo_cabeza.id).first()
    
    def obtener_ultimo(self):
        """
        Retorna (sin remover) el último vuelo de la lista (O(1)).
        
        Returns:
            Objeto Vuelo o None si la lista está vacía
        """
        if self.esta_vacia():
            return None
        
        nodo_cola = self.db.query(Nodo).get(self.lista.cola_id)
        return self.db.query(Vuelo).filter(Vuelo.nodo_id == nodo_cola.id).first()
    
    def eliminar_primero(self):
        """
        Elimina y retorna el primer vuelo de la lista (O(1)
        """
        if self.esta_vacia():
            raise ValueError("La lista está vacía")
            
        nodo_cabeza = self.db.query(Nodo).get(self.lista.cabeza_id)
        vuelo = self._eliminar_nodo(nodo_cabeza)
        self.db.commit()
        return vuelo
    
    def eliminar_ultimo(self):
        """
        Elimina y retorna el último vuelo de la lista (O(1)).
        
        Returns:
            Objeto Vuelo eliminado
        """
        if self.esta_vacia():
            raise ValueError("La lista está vacía")
            
        nodo_cola = self.db.query(Nodo).get(self.lista.cola_id)
        vuelo = self._eliminar_nodo(nodo_cola)
        self.db.commit()
        return vuelo
    
    def insertar_en_posicion(self, vuelo, posicion):
        """
        Inserta un vuelo en una posición específica de la lista (O(n)).
        
        Args:
            vuelo: Objeto Vuelo a insertar
            posicion: Índice donde insertar (0 es el primero)
            
        Returns:
            Nodo creado
            
        Raises:
            IndexError: Si la posición es inválida
        """
        if posicion < 0 or posicion > self.lista.tamanio:
            raise IndexError("Posición fuera de límites")
            
        # Caso especial: insertar al inicio
        if posicion == 0:
            return self.insertar_al_frente(vuelo)
            
        # Caso especial: insertar al final
        if posicion == self.lista.tamanio:
            return self.insertar_al_final(vuelo)
            
        # Buscar el nodo en la posición
        actual = self.db.query(Nodo).get(self.lista.cabeza_id)
        for i in range(posicion - 1):
            actual = self.db.query(Nodo).get(actual.siguiente_id)
        
        siguiente = self.db.query(Nodo).get(actual.siguiente_id)
        
        # Insertar entre actual y siguiente
        nuevo_nodo = self._crear_nodo(vuelo, anterior=actual, siguiente=siguiente)
        
        self.lista.tamanio += 1
        self.db.commit()
        return nuevo_nodo
    
    def extraer_de_posicion(self, posicion):
        """
        Elimina y retorna el vuelo en la posición dada (O(n)).
        
        Args:
            posicion: Índice del elemento a eliminar (0 es el primero)
            
        Returns:
            Objeto Vuelo en la posición dada
            
        Raises:
            IndexError: Si la posición es inválida
        """
        if self.esta_vacia() or posicion < 0 or posicion >= self.lista.tamanio:
            raise IndexError("Posición fuera de límites")
            
        # Caso especial: extraer el primero
        if posicion == 0:
            return self.eliminar_primero()
            
        # Caso especial: extraer el último
        if posicion == self.lista.tamanio - 1:
            return self.eliminar_ultimo()
            
        # Buscar el nodo en la posición
        actual = self.db.query(Nodo).get(self.lista.cabeza_id)
        for i in range(posicion):
            actual = self.db.query(Nodo).get(actual.siguiente_id)
            
        vuelo = self._eliminar_nodo(actual)
        self.db.commit()
        return vuelo
    
    def obtener_lista_completa(self):
        """
        Retorna una lista de todos los vuelos en orden (O(n)).
        
        Returns:
            Lista de objetos Vuelo
        """
        if self.esta_vacia():
            return []
            
        vuelos = []
        actual = self.db.query(Nodo).get(self.lista.cabeza_id)
        
        while actual:
            vuelo = self.db.query(Vuelo).filter(Vuelo.nodo_id == actual.id).first()
            if vuelo:
                vuelos.append(vuelo)
            actual = self.db.query(Nodo).get(actual.siguiente_id) if actual.siguiente_id else None
            
        return vuelos
    
    def reordenar_por_criterio(self, criterio_func):
        """
        Reordena la lista según un criterio específico.
        
        Args:
            criterio_func: Función que determina el orden entre dos vuelos
        """
        # Obtener todos los vuelos
        vuelos = self.obtener_lista_completa()
        
        if len(vuelos) <= 1:
            return
        
        # Eliminar todos los nodos (sin eliminar los vuelos)
        self._vaciar_lista_sin_eliminar_vuelos()
        
        # Ordenar vuelos con el criterio recibido
        vuelos_ordenados = sorted(vuelos, key=criterio_func)
        
        # Recrear la lista con los vuelos ordenados
        for vuelo in vuelos_ordenados:
            self.insertar_al_final(vuelo)
            
        self.db.commit()
    
    def _vaciar_lista_sin_eliminar_vuelos(self):
        """Elimina todos los nodos sin eliminar los vuelos asociados."""
        # Desasociar todos los vuelos de sus nodos
        vuelos = self.obtener_lista_completa()
        for vuelo in vuelos:
            vuelo.nodo_id = None
        
        # Eliminar todos los nodos
        self.db.query(Nodo).delete()
        
        # Reiniciar la lista
        self.lista.cabeza_id = None
        self.lista.cola_id = None
        self.lista.tamanio = 0
        
        self.db.flush()