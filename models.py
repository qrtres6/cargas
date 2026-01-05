from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Operacion(db.Model):
    """Registro de cada operación de carga/descarga de fichas"""
    __tablename__ = 'operaciones'

    id = db.Column(db.Integer, primary_key=True)
    usuario_destino = db.Column(db.String(100), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), default='carga')  # carga, descarga
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_proceso, completada, error
    asesor = db.Column(db.String(100), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_proceso = db.Column(db.DateTime, nullable=True)
    fecha_completado = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_destino': self.usuario_destino,
            'monto': self.monto,
            'tipo': self.tipo,
            'estado': self.estado,
            'asesor': self.asesor,
            'mensaje': self.mensaje,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_proceso': self.fecha_proceso.isoformat() if self.fecha_proceso else None,
            'fecha_completado': self.fecha_completado.isoformat() if self.fecha_completado else None
        }

class TareaCola(db.Model):
    """Cola de tareas pendientes"""
    __tablename__ = 'cola_tareas'

    id = db.Column(db.Integer, primary_key=True)
    operacion_id = db.Column(db.Integer, db.ForeignKey('operaciones.id'), nullable=False)
    prioridad = db.Column(db.Integer, default=0)
    fecha_agregada = db.Column(db.DateTime, default=datetime.utcnow)

    operacion = db.relationship('Operacion', backref='tarea_cola')

    def to_dict(self):
        return {
            'id': self.id,
            'operacion_id': self.operacion_id,
            'prioridad': self.prioridad,
            'fecha_agregada': self.fecha_agregada.isoformat() if self.fecha_agregada else None,
            'operacion': self.operacion.to_dict() if self.operacion else None
        }
