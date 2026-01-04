import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Credenciales AgentesNet
    AGENTES_URL = os.getenv('AGENTES_URL', 'https://www.agentesbet.net/agents')
    AGENTES_USER = os.getenv('AGENTES_USER')
    AGENTES_PASSWORD = os.getenv('AGENTES_PASSWORD')

    # Flask
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-cambiar-en-produccion')

    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///cargas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Bot
    HEADLESS = os.getenv('HEADLESS', 'True').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', 30000))
