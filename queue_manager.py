"""
Gestor de cola de tareas para procesar cargas de fichas secuencialmente
"""

import threading
import queue
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QueueManager:
    """Gestor de cola de tareas con procesamiento secuencial"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.cola = queue.Queue()
        self.procesando = False
        self.tarea_actual = None
        self.worker_thread = None
        self.running = False
        self.app = None
        self.bot_class = None

    def inicializar(self, app, bot_class):
        """Inicializa el gestor con la app Flask y la clase del bot"""
        self.app = app
        self.bot_class = bot_class
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("QueueManager inicializado y worker thread iniciado")

    def agregar_tarea(self, operacion_id, usuario_destino, monto, tipo='carga'):
        """Agrega una tarea a la cola"""
        tarea = {
            'tipo_tarea': 'carga',  # carga/descarga de fichas
            'operacion_id': operacion_id,
            'usuario_destino': usuario_destino,
            'monto': monto,
            'tipo': tipo,
            'fecha_agregada': datetime.utcnow()
        }
        self.cola.put(tarea)
        logger.info(f"Tarea agregada a la cola: {tarea}")
        return True

    def agregar_tarea_usuario(self, creacion_id, alias, password):
        """Agrega una tarea de creación de usuario a la cola"""
        tarea = {
            'tipo_tarea': 'crear_usuario',
            'creacion_id': creacion_id,
            'alias': alias,
            'password': password,
            'fecha_agregada': datetime.utcnow()
        }
        self.cola.put(tarea)
        logger.info(f"Tarea de creación de usuario agregada: {alias}")
        return True

    def _worker(self):
        """Worker que procesa las tareas de la cola"""
        from models import db, Operacion, CreacionUsuario

        while self.running:
            try:
                # Esperar por una tarea (timeout de 1 segundo para poder detener)
                try:
                    tarea = self.cola.get(timeout=1)
                except queue.Empty:
                    continue

                self.procesando = True
                self.tarea_actual = tarea
                logger.info(f"Procesando tarea: {tarea}")

                with self.app.app_context():
                    tipo_tarea = tarea.get('tipo_tarea', 'carga')

                    if tipo_tarea == 'crear_usuario':
                        # Procesar creación de usuario
                        self._procesar_creacion_usuario(tarea, db, CreacionUsuario)
                    else:
                        # Procesar carga/descarga de fichas
                        self._procesar_carga(tarea, db, Operacion)

                self.cola.task_done()
                self.tarea_actual = None
                self.procesando = False

            except Exception as e:
                logger.error(f"Error en worker: {e}")
                self.procesando = False
                self.tarea_actual = None

    def _procesar_carga(self, tarea, db, Operacion):
        """Procesa una tarea de carga/descarga de fichas"""
        operacion = Operacion.query.get(tarea['operacion_id'])
        if operacion:
            operacion.estado = 'en_proceso'
            operacion.fecha_proceso = datetime.utcnow()
            db.session.commit()

        try:
            bot = self.bot_class()
            resultado = bot.ejecutar_carga_completa(
                tarea['usuario_destino'],
                tarea['monto'],
                tarea.get('tipo', 'carga')
            )

            if operacion:
                if resultado['success']:
                    operacion.estado = 'completada'
                    operacion.mensaje = resultado['message']
                else:
                    operacion.estado = 'error'
                    operacion.mensaje = resultado['message']
                operacion.fecha_completado = datetime.utcnow()
                db.session.commit()

        except Exception as e:
            logger.error(f"Error ejecutando bot: {e}")
            if operacion:
                operacion.estado = 'error'
                operacion.mensaje = str(e)
                operacion.fecha_completado = datetime.utcnow()
                db.session.commit()

    def _procesar_creacion_usuario(self, tarea, db, CreacionUsuario):
        """Procesa una tarea de creación de usuario"""
        creacion = CreacionUsuario.query.get(tarea['creacion_id'])
        if creacion:
            creacion.estado = 'en_proceso'
            creacion.fecha_proceso = datetime.utcnow()
            db.session.commit()

        try:
            bot = self.bot_class()
            resultado = bot.ejecutar_creacion_usuario(
                tarea['alias'],
                tarea['password']
            )

            if creacion:
                if resultado['success']:
                    creacion.estado = 'completada'
                    creacion.alias_final = resultado.get('alias_final', tarea['alias'])
                    creacion.mensaje = resultado['message']
                else:
                    creacion.estado = 'error'
                    creacion.mensaje = resultado['message']
                creacion.fecha_completado = datetime.utcnow()
                db.session.commit()

        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            if creacion:
                creacion.estado = 'error'
                creacion.mensaje = str(e)
                creacion.fecha_completado = datetime.utcnow()
                db.session.commit()

    def obtener_estado(self):
        """Obtiene el estado actual de la cola"""
        return {
            'procesando': self.procesando,
            'tarea_actual': self.tarea_actual,
            'tareas_pendientes': self.cola.qsize()
        }

    def detener(self):
        """Detiene el worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("QueueManager detenido")


# Instancia global
queue_manager = QueueManager()
