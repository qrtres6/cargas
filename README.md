# Sistema de Carga de Fichas

Sistema automatizado para cargar fichas a usuarios en AgentesNet.

## Características

- **Interfaz web para asesores**: Formulario simple para solicitar cargas
- **Cola de tareas**: Procesa cargas secuencialmente
- **Automatización**: Bot que realiza login y carga de fichas automáticamente
- **Registro completo**: Historial de todas las operaciones
- **Estadísticas**: Dashboard con métricas en tiempo real

## Requisitos

- Python 3.8+
- Chromium (instalado automáticamente por Playwright)

## Instalación

```bash
# 1. Dar permisos de ejecución
chmod +x setup.sh run.sh

# 2. Ejecutar instalación
./setup.sh
```

## Uso

```bash
# Iniciar el servidor
./run.sh
```

Accede a la interfaz web en: http://localhost:5000

## Configuración

Edita el archivo `.env` para configurar:

```env
# Credenciales de AgentesNet
AGENTES_URL=https://www.agentesbet.net/agents
AGENTES_USER=tu_usuario
AGENTES_PASSWORD=tu_contraseña

# Servidor
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Bot
HEADLESS=True  # False para ver el navegador
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Interfaz web principal |
| POST | `/api/cargar` | Solicitar carga de fichas |
| GET | `/api/estado` | Estado de la cola |
| GET | `/api/operaciones` | Listar operaciones |
| GET | `/api/estadisticas` | Obtener estadísticas |
| GET | `/api/cola` | Ver cola de tareas |
| GET | `/api/health` | Health check |

### Ejemplo: Cargar fichas

```bash
curl -X POST http://localhost:5000/api/cargar \
  -H "Content-Type: application/json" \
  -d '{"usuario": "nombre_usuario", "monto": 100, "asesor": "Juan"}'
```

## Estructura del Proyecto

```
cargas/
├── app.py              # Aplicación principal Flask
├── bot.py              # Bot de automatización
├── config.py           # Configuración
├── models.py           # Modelos de base de datos
├── queue_manager.py    # Gestor de cola de tareas
├── requirements.txt    # Dependencias Python
├── setup.sh            # Script de instalación
├── run.sh              # Script de ejecución
├── .env                # Variables de entorno
├── templates/          # Templates HTML
│   └── index.html
└── static/             # Archivos estáticos
    ├── css/
    │   └── styles.css
    └── js/
        └── app.js
```

## Seguridad

- Las credenciales se almacenan en `.env` (no en git)
- El archivo `.env` está en `.gitignore`
- Se recomienda usar HTTPS en producción
