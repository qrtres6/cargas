"""
Aplicación principal Flask para el sistema de carga de fichas
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import logging

from config import Config
from models import db, Operacion, TareaCola
from queue_manager import queue_manager
from bot import AgentesNetBot

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)
app.config.from_object(Config)
CORS(app)

# Inicializar base de datos
db.init_app(app)

# Crear tablas al iniciar
with app.app_context():
    db.create_all()
    logger.info("Base de datos inicializada")

# Inicializar queue manager
queue_manager.inicializar(app, AgentesNetBot)


# ============== RUTAS DE API ==============

@app.route('/')
def index():
    """Página principal del asesor"""
    return render_template('index.html')


@app.route('/api/cargar', methods=['POST'])
def cargar_fichas():
    """
    Endpoint para solicitar carga de fichas
    Body: { "usuario": "nombre_usuario", "monto": 100, "asesor": "nombre_asesor" }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

        usuario = data.get('usuario', '').strip()
        monto = data.get('monto')
        asesor = data.get('asesor', 'Sistema').strip()

        # Validaciones
        if not usuario:
            return jsonify({'success': False, 'error': 'El usuario es requerido'}), 400

        if not monto or monto <= 0:
            return jsonify({'success': False, 'error': 'El monto debe ser mayor a 0'}), 400

        try:
            monto = float(monto)
        except ValueError:
            return jsonify({'success': False, 'error': 'El monto debe ser un número válido'}), 400

        # Crear operación en base de datos
        operacion = Operacion(
            usuario_destino=usuario,
            monto=monto,
            estado='pendiente',
            asesor=asesor
        )
        db.session.add(operacion)
        db.session.commit()

        # Agregar a la cola de tareas
        queue_manager.agregar_tarea(
            operacion_id=operacion.id,
            usuario_destino=usuario,
            monto=monto
        )

        logger.info(f"Nueva carga solicitada: {usuario} - {monto} fichas por {asesor}")

        return jsonify({
            'success': True,
            'message': 'Carga agregada a la cola',
            'operacion_id': operacion.id,
            'posicion_cola': queue_manager.obtener_estado()['tareas_pendientes']
        })

    except Exception as e:
        logger.error(f"Error en /api/cargar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/estado', methods=['GET'])
def estado_cola():
    """Obtiene el estado actual de la cola de tareas"""
    try:
        estado = queue_manager.obtener_estado()
        return jsonify({
            'success': True,
            'estado': estado
        })
    except Exception as e:
        logger.error(f"Error en /api/estado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/operaciones', methods=['GET'])
def listar_operaciones():
    """Lista todas las operaciones con filtros opcionales"""
    try:
        estado = request.args.get('estado')
        limite = request.args.get('limite', 50, type=int)
        pagina = request.args.get('pagina', 1, type=int)

        query = Operacion.query.order_by(Operacion.fecha_creacion.desc())

        if estado:
            query = query.filter_by(estado=estado)

        # Paginación
        total = query.count()
        operaciones = query.offset((pagina - 1) * limite).limit(limite).all()

        return jsonify({
            'success': True,
            'operaciones': [op.to_dict() for op in operaciones],
            'total': total,
            'pagina': pagina,
            'limite': limite
        })

    except Exception as e:
        logger.error(f"Error en /api/operaciones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/operacion/<int:operacion_id>', methods=['GET'])
def obtener_operacion(operacion_id):
    """Obtiene los detalles de una operación específica"""
    try:
        operacion = Operacion.query.get(operacion_id)

        if not operacion:
            return jsonify({'success': False, 'error': 'Operación no encontrada'}), 404

        return jsonify({
            'success': True,
            'operacion': operacion.to_dict()
        })

    except Exception as e:
        logger.error(f"Error en /api/operacion/{operacion_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    """Obtiene estadísticas de las operaciones"""
    try:
        total = Operacion.query.count()
        completadas = Operacion.query.filter_by(estado='completada').count()
        pendientes = Operacion.query.filter_by(estado='pendiente').count()
        en_proceso = Operacion.query.filter_by(estado='en_proceso').count()
        errores = Operacion.query.filter_by(estado='error').count()

        # Total de fichas cargadas (solo completadas)
        from sqlalchemy import func
        total_fichas = db.session.query(
            func.sum(Operacion.monto)
        ).filter_by(estado='completada').scalar() or 0

        return jsonify({
            'success': True,
            'estadisticas': {
                'total': total,
                'completadas': completadas,
                'pendientes': pendientes,
                'en_proceso': en_proceso,
                'errores': errores,
                'total_fichas_cargadas': float(total_fichas)
            }
        })

    except Exception as e:
        logger.error(f"Error en /api/estadisticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cola', methods=['GET'])
def ver_cola():
    """Obtiene las tareas en cola pendientes"""
    try:
        pendientes = Operacion.query.filter(
            Operacion.estado.in_(['pendiente', 'en_proceso'])
        ).order_by(Operacion.fecha_creacion.asc()).all()

        estado_cola = queue_manager.obtener_estado()

        return jsonify({
            'success': True,
            'cola': [op.to_dict() for op in pendientes],
            'estado_procesamiento': estado_cola
        })

    except Exception as e:
        logger.error(f"Error en /api/cola: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de salud del sistema"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'queue_status': queue_manager.obtener_estado()
    })


# ============== MANEJO DE ERRORES ==============

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Recurso no encontrado'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


# ============== INICIO DE LA APLICACIÓN ==============

if __name__ == '__main__':
    logger.info(f"Iniciando servidor en {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
