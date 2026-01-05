"""
Aplicación principal Flask para el sistema de carga de fichas
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_cors import CORS
from datetime import datetime
import os
import logging
import hashlib

from config import Config

# Contraseña de admin (cambiar en producción)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
from models import db, Operacion, TareaCola, CreacionUsuario
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
    Endpoint para solicitar carga/descarga de fichas
    Body: { "usuario": "nombre_usuario", "monto": 100, "tipo": "carga|descarga" }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

        usuario = data.get('usuario', '').strip().lower()
        monto = data.get('monto')
        tipo = data.get('tipo', 'carga').strip()
        asesor = data.get('asesor', 'Sistema').strip()

        # Validaciones
        if not usuario:
            return jsonify({'success': False, 'error': 'El usuario es requerido'}), 400

        if not monto or monto <= 0:
            return jsonify({'success': False, 'error': 'El monto debe ser mayor a 0'}), 400

        if tipo not in ['carga', 'descarga']:
            return jsonify({'success': False, 'error': 'El tipo debe ser "carga" o "descarga"'}), 400

        try:
            monto = float(monto)
        except ValueError:
            return jsonify({'success': False, 'error': 'El monto debe ser un número válido'}), 400

        # Crear operación en base de datos
        operacion = Operacion(
            usuario_destino=usuario,
            monto=monto,
            tipo=tipo,
            estado='pendiente',
            asesor=asesor
        )
        db.session.add(operacion)
        db.session.commit()

        # Agregar a la cola de tareas
        queue_manager.agregar_tarea(
            operacion_id=operacion.id,
            usuario_destino=usuario,
            monto=monto,
            tipo=tipo
        )

        accion = 'Carga' if tipo == 'carga' else 'Descarga'
        logger.info(f"Nueva {accion.lower()} solicitada: {usuario} - {monto} fichas por {asesor}")

        return jsonify({
            'success': True,
            'message': f'{accion} agregada a la cola',
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


@app.route('/api/crear-usuario', methods=['POST'])
def crear_usuario():
    """
    Endpoint para solicitar creación de usuario
    Body: { "alias": "nombre_usuario", "password": "contraseña" }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

        alias = data.get('alias', '').strip().lower()
        password = data.get('password', '').strip()
        usar_password_rapido = data.get('password_rapido', False)

        # Validaciones
        if not alias:
            return jsonify({'success': False, 'error': 'El alias es requerido'}), 400

        # Si usa password rápido, usar 1122casino
        if usar_password_rapido or not password:
            password = '1122casino'

        # Crear registro en base de datos
        creacion = CreacionUsuario(
            alias_solicitado=alias,
            password=password,
            estado='pendiente'
        )
        db.session.add(creacion)
        db.session.commit()

        # Agregar a la cola de tareas
        queue_manager.agregar_tarea_usuario(
            creacion_id=creacion.id,
            alias=alias,
            password=password
        )

        logger.info(f"Nueva creación de usuario solicitada: {alias}")

        return jsonify({
            'success': True,
            'message': 'Creación de usuario agregada a la cola',
            'creacion_id': creacion.id,
            'posicion_cola': queue_manager.obtener_estado()['tareas_pendientes']
        })

    except Exception as e:
        logger.error(f"Error en /api/crear-usuario: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    """Lista todas las creaciones de usuarios con filtros opcionales"""
    try:
        estado = request.args.get('estado')
        limite = request.args.get('limite', 50, type=int)
        pagina = request.args.get('pagina', 1, type=int)

        query = CreacionUsuario.query.order_by(CreacionUsuario.fecha_creacion.desc())

        if estado:
            query = query.filter_by(estado=estado)

        # Paginación
        total = query.count()
        creaciones = query.offset((pagina - 1) * limite).limit(limite).all()

        return jsonify({
            'success': True,
            'usuarios': [c.to_dict() for c in creaciones],
            'total': total,
            'pagina': pagina,
            'limite': limite
        })

    except Exception as e:
        logger.error(f"Error en /api/usuarios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cola-usuarios', methods=['GET'])
def ver_cola_usuarios():
    """Obtiene las creaciones de usuario en cola pendientes"""
    try:
        pendientes = CreacionUsuario.query.filter(
            CreacionUsuario.estado.in_(['pendiente', 'en_proceso'])
        ).order_by(CreacionUsuario.fecha_creacion.asc()).all()

        return jsonify({
            'success': True,
            'cola': [c.to_dict() for c in pendientes]
        })

    except Exception as e:
        logger.error(f"Error en /api/cola-usuarios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de salud del sistema"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'queue_status': queue_manager.obtener_estado()
    })


@app.route('/api/login-status', methods=['GET'])
def login_status():
    """Obtiene el estado actual del login"""
    try:
        is_logged = AgentesNetBot.is_logged_in()
        return jsonify({
            'success': True,
            'logged_in': is_logged
        })
    except Exception as e:
        logger.error(f"Error en /api/login-status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/force-login', methods=['POST'])
def force_login():
    """Fuerza el login en AgentesNet"""
    try:
        bot = AgentesNetBot()
        resultado = bot.force_login()
        return jsonify({
            'success': resultado.get('success', False),
            'message': resultado.get('message', ''),
            'logged_in': AgentesNetBot.is_logged_in()
        })
    except Exception as e:
        logger.error(f"Error en /api/force-login: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/force-logout', methods=['POST'])
def force_logout():
    """Fuerza el cierre de sesión"""
    try:
        resultado = AgentesNetBot.force_logout()
        return jsonify({
            'success': True,
            'message': resultado.get('message', 'Sesión cerrada'),
            'logged_in': False
        })
    except Exception as e:
        logger.error(f"Error en /api/force-logout: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buscar-retiros', methods=['POST'])
def buscar_retiros():
    """Busca retiros recientes de un usuario"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

        usuario = data.get('usuario', '').strip().lower()

        if not usuario:
            return jsonify({'success': False, 'error': 'El usuario es requerido'}), 400

        bot = AgentesNetBot()
        resultado = bot.buscar_retiros_usuario(usuario)

        return jsonify(resultado)

    except Exception as e:
        logger.error(f"Error en /api/buscar-retiros: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== PANEL DE ADMINISTRACIÓN ==============

def get_stats():
    """Obtiene estadísticas para el panel admin"""
    return {
        'total': Operacion.query.count(),
        'completadas': Operacion.query.filter_by(estado='completada').count(),
        'pendientes': Operacion.query.filter_by(estado='pendiente').count(),
        'en_proceso': Operacion.query.filter_by(estado='en_proceso').count(),
        'errores': Operacion.query.filter_by(estado='error').count()
    }

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Página de login del admin"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Contraseña incorrecta')

    # Si ya está logueado, ir al panel
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))

    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    """Panel de administración"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    message = request.args.get('message')
    stats = get_stats()
    return render_template('admin.html', stats=stats, message=message)

@app.route('/admin/logout')
def admin_logout():
    """Cerrar sesión de admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/delete-completed', methods=['POST'])
def delete_completed():
    """Eliminar operaciones completadas"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    try:
        count = Operacion.query.filter_by(estado='completada').delete()
        db.session.commit()
        logger.info(f"Admin eliminó {count} operaciones completadas")
        return redirect(url_for('admin_panel', message=f'Se eliminaron {count} operaciones completadas'))
    except Exception as e:
        logger.error(f"Error eliminando completadas: {e}")
        db.session.rollback()
        return redirect(url_for('admin_panel', message=f'Error: {str(e)}'))

@app.route('/admin/delete-errors', methods=['POST'])
def delete_errors():
    """Eliminar operaciones con error"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    try:
        count = Operacion.query.filter_by(estado='error').delete()
        db.session.commit()
        logger.info(f"Admin eliminó {count} operaciones con error")
        return redirect(url_for('admin_panel', message=f'Se eliminaron {count} operaciones con error'))
    except Exception as e:
        logger.error(f"Error eliminando errores: {e}")
        db.session.rollback()
        return redirect(url_for('admin_panel', message=f'Error: {str(e)}'))

@app.route('/admin/delete-all', methods=['POST'])
def delete_all():
    """Eliminar todo el historial"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    try:
        # Primero eliminar tareas de cola
        TareaCola.query.delete()
        # Luego eliminar operaciones
        count = Operacion.query.delete()
        db.session.commit()
        logger.info(f"Admin eliminó TODO el historial ({count} operaciones)")
        return redirect(url_for('admin_panel', message=f'Se eliminó todo el historial ({count} operaciones)'))
    except Exception as e:
        logger.error(f"Error eliminando historial: {e}")
        db.session.rollback()
        return redirect(url_for('admin_panel', message=f'Error: {str(e)}'))


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
